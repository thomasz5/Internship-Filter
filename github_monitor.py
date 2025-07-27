#!/usr/bin/env python3
"""
GitHub Monitor for Internship Repositories
Monitors SimplifyJobs and speedyapply repos for new internship postings
"""

import git
import os
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import logging
from config import Config

class InternshipGitHubMonitor:
    def __init__(self):
        self.config = Config()
        self.repos_dir = "monitored_repos"
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Setup SQLite database for tracking internships"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS internships (
                id INTEGER PRIMARY KEY,
                company TEXT,
                role TEXT,
                location TEXT,
                application_link TEXT,
                source_repo TEXT,
                discovered_date TEXT,
                commit_hash TEXT,
                UNIQUE(company, role, application_link)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY,
                name TEXT,
                title TEXT,
                company TEXT,
                linkedin_url TEXT,
                college_match INTEGER,
                discovered_date TEXT,
                UNIQUE(linkedin_url)
            )
        ''')
        conn.commit()
        conn.close()
    
    def clone_or_update_repos(self):
        """Clone or update the monitored repositories"""
        if not os.path.exists(self.repos_dir):
            os.makedirs(self.repos_dir)
        
        new_internships = []
        
        for repo_url in self.config.GITHUB_REPOS:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            repo_path = os.path.join(self.repos_dir, repo_name)
            
            try:
                if os.path.exists(repo_path):
                    # Pull latest changes
                    repo = git.Repo(repo_path)
                    old_commit = repo.head.commit.hexsha
                    repo.remotes.origin.pull()
                    new_commit = repo.head.commit.hexsha
                    
                    if old_commit != new_commit:
                        self.logger.info(f"New commits found in {repo_name}")
                        # Get commits since last check
                        commits = list(repo.iter_commits(f'{old_commit}..{new_commit}'))
                        new_internships.extend(self.parse_new_commits(repo, commits, repo_name))
                    else:
                        self.logger.info(f"No new commits in {repo_name}")
                else:
                    # Clone repository
                    self.logger.info(f"Cloning {repo_name}")
                    repo = git.Repo.clone_from(repo_url, repo_path)
                    # Parse recent commits for initial setup
                    recent_commits = list(repo.iter_commits(max_count=10))
                    new_internships.extend(self.parse_new_commits(repo, recent_commits, repo_name))
                    
            except Exception as e:
                self.logger.error(f"Error with repository {repo_name}: {e}")
        
        return new_internships
    
    def parse_new_commits(self, repo, commits, repo_name: str) -> List[Dict]:
        """Parse commits for new internship postings"""
        new_internships = []
        
        for commit in commits:
            # Check if commit message suggests new internship
            if self.is_internship_commit(commit.message):
                self.logger.info(f"Potential internship commit: {commit.message[:100]}")
                
                # Parse the README or main files for new entries
                try:
                    # Get the README content from this commit
                    readme_content = ""
                    for item in commit.tree.traverse():
                        if item.name.lower() == 'readme.md':
                            readme_content = item.data_stream.read().decode('utf-8')
                            break
                    
                    if readme_content:
                        internships = self.parse_readme_for_internships(readme_content, repo_name, commit.hexsha)
                        new_internships.extend(internships)
                        
                except Exception as e:
                    self.logger.error(f"Error parsing commit {commit.hexsha}: {e}")
        
        return new_internships
    
    def is_internship_commit(self, commit_message: str) -> bool:
        """Check if commit message indicates new internship posting"""
        message_lower = commit_message.lower()
        
        # Common patterns in internship repo commits
        internship_indicators = [
            'add', 'new', 'update', 'intern', 'role', 'position', 
            'company', 'job', 'opening', 'hiring'
        ]
        
        return any(indicator in message_lower for indicator in internship_indicators)
    
    def parse_readme_for_internships(self, content: str, repo_name: str, commit_hash: str) -> List[Dict]:
        """Parse README content for internship listings"""
        internships = []
        
        # For SimplifyJobs format: | Company | Role | Location | Application | Age |
        if "SimplifyJobs" in repo_name:
            internships.extend(self._parse_simplify_jobs_format(content, repo_name, commit_hash))
        
        # For speedyapply format (may be different)
        elif "speedyapply" in repo_name:
            internships.extend(self._parse_speedyapply_format(content, repo_name, commit_hash))
        
        return internships
    
    def _parse_simplify_jobs_format(self, content: str, repo_name: str, commit_hash: str) -> List[Dict]:
        """Parse SimplifyJobs markdown table format"""
        internships = []
        
        # Look for markdown table rows
        lines = content.split('\n')
        current_section = ""
        
        for line in lines:
            # Track current section
            if line.startswith('##') and any(keyword in line.lower() for keyword in ['software', 'data', 'engineer']):
                current_section = line.strip()
                continue
            
            # Parse table rows (format: | Company | Role | Location | Application | Age |)
            if line.startswith('| **[') or line.startswith('| ↳'):
                try:
                    internship = self._parse_table_row(line, repo_name, commit_hash, current_section)
                    if internship and self._is_relevant_internship(internship):
                        internships.append(internship)
                except Exception as e:
                    self.logger.debug(f"Error parsing line: {line[:50]}... - {e}")
        
        return internships
    
    def _parse_table_row(self, line: str, repo_name: str, commit_hash: str, section: str) -> Optional[Dict]:
        """Parse a single table row"""
        # Split by | and clean up
        parts = [part.strip() for part in line.split('|')]
        
        if len(parts) < 5:
            return None
        
        company_part = parts[1]
        role_part = parts[2]
        location_part = parts[3]
        application_part = parts[4]
        
        # Extract company name
        company_match = re.search(r'\*\*\[(.*?)\]', company_part)
        company = company_match.group(1) if company_match else company_part.strip()
        
        # Handle continuation rows (↳)
        if company_part.strip() == '↳':
            company = "Previous Company"  # Will need context from previous row
        
        # Extract application link
        app_link_match = re.search(r'\[Apply\]\((.*?)\)', application_part)
        app_link = app_link_match.group(1) if app_link_match else ""
        
        return {
            'company': company,
            'role': role_part.strip(),
            'location': location_part.strip(),
            'application_link': app_link,
            'source_repo': repo_name,
            'commit_hash': commit_hash,
            'section': section,
            'discovered_date': datetime.now().isoformat()
        }
    
    def _parse_speedyapply_format(self, content: str, repo_name: str, commit_hash: str) -> List[Dict]:
        """Parse speedyapply format (implement based on their structure)"""
        # This would need to be customized based on their specific format
        # For now, return empty list - you can extend this based on their README structure
        return []
    
    def _is_relevant_internship(self, internship: Dict) -> bool:
        """Check if internship is relevant based on location and role"""
        role_lower = internship['role'].lower()
        location_lower = internship['location'].lower()
        
        # Check if it's an internship
        if not any(keyword in role_lower for keyword in self.config.INTERNSHIP_KEYWORDS):
            return False
        
        # Prioritize Seattle area and US positions
        if any(loc.lower() in location_lower for loc in self.config.PREFERRED_LOCATIONS):
            return True
        
        # Also include remote and general US positions
        if 'remote' in location_lower or 'united states' in location_lower:
            return True
        
        return False
    
    def save_internships(self, internships: List[Dict]):
        """Save new internships to database"""
        if not internships:
            return
        
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        for internship in internships:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO internships 
                    (company, role, location, application_link, source_repo, discovered_date, commit_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    internship['company'],
                    internship['role'],
                    internship['location'],
                    internship['application_link'],
                    internship['source_repo'],
                    internship['discovered_date'],
                    internship['commit_hash']
                ))
                self.logger.info(f"Saved new internship: {internship['company']} - {internship['role']}")
                
            except sqlite3.IntegrityError:
                # Already exists
                pass
        
        conn.commit()
        conn.close()
    
    def get_companies_with_new_internships(self) -> List[str]:
        """Get list of companies that have new internships"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        cursor = conn.execute('''
            SELECT DISTINCT company FROM internships 
            WHERE discovered_date > datetime('now', '-1 day')
        ''')
        companies = [row[0] for row in cursor.fetchall()]
        conn.close()
        return companies
    
    def run_monitor(self):
        """Main monitoring function"""
        self.logger.info("Starting GitHub repository monitoring")
        
        try:
            new_internships = self.clone_or_update_repos()
            
            if new_internships:
                self.logger.info(f"Found {len(new_internships)} new internships")
                self.save_internships(new_internships)
                
                # Print summary
                print(f"\n🎉 Found {len(new_internships)} new internship opportunities!")
                for internship in new_internships[:10]:  # Show first 10
                    print(f"• {internship['company']} - {internship['role']}")
                
                if len(new_internships) > 10:
                    print(f"• ... and {len(new_internships) - 10} more!")
                
                return [internship['company'] for internship in new_internships]
            else:
                self.logger.info("No new internships found")
                print("No new internships found in this check.")
                return []
                
        except Exception as e:
            self.logger.error(f"Error in monitoring: {e}")
            return []

if __name__ == "__main__":
    monitor = InternshipGitHubMonitor()
    monitor.run_monitor() 