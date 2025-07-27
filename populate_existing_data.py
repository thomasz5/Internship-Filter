#!/usr/bin/env python3
"""
Populate database with existing internships for testing Excel integration
"""

import sqlite3
import re
from datetime import datetime
from config import Config

def parse_current_internships():
    """Parse current internships from the README file"""
    config = Config()
    
    # Read the SimplifyJobs README
    readme_path = "monitored_repos/Summer2026-Internships/README.md"
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("README file not found. Please run GitHub monitoring first.")
        return []
    
    internships = []
    lines = content.split('\n')
    
    for line in lines:
        # Look for table rows with internship data
        if line.startswith('| **[') and '|' in line:
            try:
                parts = [part.strip() for part in line.split('|')]
                
                if len(parts) >= 5:
                    company_part = parts[1]
                    role_part = parts[2]  
                    location_part = parts[3]
                    application_part = parts[4]
                    
                    # Extract company name
                    company_match = re.search(r'\*\*\[(.*?)\]', company_part)
                    company = company_match.group(1) if company_match else company_part.strip()
                    
                    # Skip if continuation row
                    if company_part.strip() == '↳':
                        continue
                    
                    # Extract application link
                    app_link_match = re.search(r'\[Apply\]\((.*?)\)', application_part)
                    app_link = app_link_match.group(1) if app_link_match else ""
                    
                    # Check if it's relevant (Seattle, Remote, or US-based)
                    location_lower = location_part.lower()
                    if any(loc in location_lower for loc in ['seattle', 'remote', 'united states', 'bellevue', 'redmond']):
                        internships.append({
                            'company': company,
                            'role': role_part.strip(),
                            'location': location_part.strip(),
                            'application_link': app_link,
                            'source_repo': 'Summer2026-Internships',
                            'discovered_date': datetime.now().isoformat(),
                            'commit_hash': 'initial_load'
                        })
                        
            except Exception as e:
                print(f"Error parsing line: {e}")
                continue
    
    return internships

def save_to_database(internships):
    """Save internships to database"""
    config = Config()
    conn = sqlite3.connect(config.DATABASE_PATH)
    
    saved_count = 0
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
            saved_count += 1
        except Exception as e:
            print(f"Error saving internship: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"💾 Saved {saved_count} internships to database")
    return saved_count

def main():
    print("📚 Parsing existing internships from repository...")
    internships = parse_current_internships()
    
    if internships:
        print(f"✅ Found {len(internships)} relevant internship opportunities")
        
        # Show a few examples
        print("\n📋 Examples of what was found:")
        for i, internship in enumerate(internships[:5]):
            print(f"   {i+1}. {internship['company']} - {internship['role']} ({internship['location']})")
        
        if len(internships) > 5:
            print(f"   ... and {len(internships) - 5} more!")
        
        # Save to database
        saved_count = save_to_database(internships)
        
        if saved_count > 0:
            print(f"\n🎉 Successfully added {saved_count} internships!")
            print("📊 Now run 'python main.py excel' to see them in your Excel spreadsheet!")
        
    else:
        print("❌ No relevant internships found")

if __name__ == "__main__":
    main() 