#!/usr/bin/env python3
"""
UW Internship Finder - Main Application
Monitors GitHub repos for new internships and finds UW alumni at those companies
"""

import argparse
import schedule
import time
import sys
import sqlite3
import csv
from datetime import datetime
from typing import List, Dict
import logging
from config import Config
from github_monitor import InternshipGitHubMonitor
from linkedin_scraper import UWLinkedInScraper
from excel_integration import ExcelIntegration

class UWInternshipFinder:
    def __init__(self):
        self.config = Config()
        self.github_monitor = InternshipGitHubMonitor()
        self.linkedin_scraper = UWLinkedInScraper()
        self.excel_integration = ExcelIntegration()
        self.setup_logging()
    
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
    
    def run_full_cycle(self):
        """Run a complete monitoring cycle"""
        print(f"\n🔍 Starting internship monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Monitor GitHub for new internships
        print("\n📚 Step 1: Monitoring GitHub repositories for new internships...")
        new_companies = self.github_monitor.run_monitor()
        
        # Step 2: If new companies found, search for UW alumni
        data_updated = False
        if new_companies:
            print(f"\n🎓 Step 2: Searching for UW alumni at {len(set(new_companies))} companies...")
            unique_companies = list(set(new_companies))  # Remove duplicates
            
            # Limit to prevent overwhelming LinkedIn
            if len(unique_companies) > 10:
                print(f"⚠️  Limiting search to first 10 companies to be respectful to LinkedIn")
                unique_companies = unique_companies[:10]
            
            self.linkedin_scraper.scrape_companies(unique_companies)
            data_updated = True
        else:
            print("\n✨ No new internships found, so no LinkedIn scraping needed.")
        
        # Step 3: Update Excel if any new data was found
        if new_companies or data_updated:
            print(f"\n📊 Step 3: Updating Excel spreadsheet...")
            success = self.excel_integration.create_or_update_excel()
            if success:
                # Add notification about new findings
                if new_companies:
                    self.excel_integration.add_notification_to_excel(
                        f"Found {len(new_companies)} new internship opportunities!"
                    )
        
        print(f"\n✅ Monitoring cycle completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def export_opportunities_to_csv(self):
        """Export found opportunities to CSV for easy viewing"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        # Query to join internships with profiles
        query = '''
        SELECT 
            i.company,
            i.role,
            i.location,
            i.application_link,
            i.discovered_date as internship_date,
            p.name,
            p.title,
            p.linkedin_url,
            p.discovered_date as profile_date
        FROM internships i
        LEFT JOIN profiles p ON i.company = p.company
        ORDER BY i.discovered_date DESC, p.discovered_date DESC
        '''
        
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            with open(self.config.OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Company', 'Internship Role', 'Location', 'Application Link',
                    'Internship Found Date', 'UW Alumni Name', 'Alumni Title', 
                    'LinkedIn Profile', 'Alumni Found Date'
                ])
                writer.writerows(rows)
            
            print(f"📊 Exported {len(rows)} opportunities to {self.config.OUTPUT_CSV}")
        else:
            print("📊 No opportunities found to export")
        
        conn.close()
    
    def show_summary(self):
        """Show summary of findings"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        # Count internships
        internship_count = conn.execute('SELECT COUNT(*) FROM internships').fetchone()[0]
        
        # Count profiles
        profile_count = conn.execute('SELECT COUNT(*) FROM profiles').fetchone()[0]
        
        # Recent internships (last 7 days)
        recent_internships = conn.execute('''
            SELECT COUNT(*) FROM internships 
            WHERE discovered_date > datetime('now', '-7 days')
        ''').fetchone()[0]
        
        # Recent profiles (last 7 days)
        recent_profiles = conn.execute('''
            SELECT COUNT(*) FROM profiles 
            WHERE discovered_date > datetime('now', '-7 days')
        ''').fetchone()[0]
        
        # Top companies with most internships
        top_companies = conn.execute('''
            SELECT company, COUNT(*) as count 
            FROM internships 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 5
        ''').fetchall()
        
        print("\n📈 SUMMARY REPORT")
        print("=" * 40)
        print(f"Total Internships Found: {internship_count}")
        print(f"Total UW Alumni Found: {profile_count}")
        print(f"New This Week: {recent_internships} internships, {recent_profiles} alumni")
        
        if top_companies:
            print("\nTop Companies by Internship Count:")
            for company, count in top_companies:
                print(f"  • {company}: {count} internships")
        
        conn.close()
    
    def list_recent_opportunities(self, days: int = 7):
        """List recent opportunities"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        query = '''
        SELECT company, role, location, application_link, discovered_date
        FROM internships 
        WHERE discovered_date > datetime('now', '-{} days')
        ORDER BY discovered_date DESC
        '''.format(days)
        
        cursor = conn.execute(query)
        opportunities = cursor.fetchall()
        
        if opportunities:
            print(f"\n🆕 Recent Internship Opportunities (Last {days} days):")
            print("-" * 60)
            for company, role, location, app_link, date in opportunities:
                print(f"🏢 {company}")
                print(f"   Role: {role}")
                print(f"   Location: {location}")
                print(f"   Apply: {app_link}")
                print(f"   Found: {date}")
                print()
        else:
            print(f"No new opportunities found in the last {days} days.")
        
        conn.close()
    
    def list_uw_alumni(self, company: str = None):
        """List found UW alumni"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        if company:
            query = '''
            SELECT name, title, company, linkedin_url, discovered_date
            FROM profiles 
            WHERE company LIKE ?
            ORDER BY discovered_date DESC
            '''
            cursor = conn.execute(query, (f'%{company}%',))
        else:
            query = '''
            SELECT name, title, company, linkedin_url, discovered_date
            FROM profiles 
            ORDER BY discovered_date DESC
            LIMIT 20
            '''
            cursor = conn.execute(query)
        
        alumni = cursor.fetchall()
        
        if alumni:
            print(f"\n🎓 UW Alumni Found{f' at {company}' if company else ' (Most Recent 20)'}:")
            print("-" * 60)
            for name, title, company, linkedin_url, date in alumni:
                print(f"👤 {name}")
                print(f"   Title: {title}")
                print(f"   Company: {company}")
                print(f"   LinkedIn: {linkedin_url}")
                print(f"   Found: {date}")
                print()
        else:
            search_term = f"at {company}" if company else ""
            print(f"No UW alumni found {search_term}.")
        
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='UW Internship Finder - Monitor internships and find UW alumni')
    parser.add_argument('command', choices=[
        'run', 'monitor', 'summary', 'recent', 'alumni', 'export', 'excel', 'github-only', 'linkedin-only'
    ], help='Command to execute')
    parser.add_argument('--company', type=str, help='Company name for alumni search')
    parser.add_argument('--days', type=int, default=7, help='Number of days for recent search')
    parser.add_argument('--companies', nargs='+', help='Specific companies to scrape LinkedIn for')
    
    args = parser.parse_args()
    
    finder = UWInternshipFinder()
    
    if args.command == 'run':
        # Run one complete cycle
        finder.run_full_cycle()
        finder.export_opportunities_to_csv()
        
        # Always update Excel on manual run
        print("\n📊 Updating Excel spreadsheet...")
        finder.excel_integration.create_or_update_excel()
        
        finder.show_summary()
    
    elif args.command == 'monitor':
        # Start continuous monitoring
        print("🔄 Starting continuous monitoring (every 12 hours)")
        print("Press Ctrl+C to stop")
        
        # Schedule the job
        schedule.every(finder.config.CHECK_INTERVAL_HOURS).hours.do(finder.run_full_cycle)
        
        # Run immediately once
        finder.run_full_cycle()
        
        # Then wait for scheduled runs
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
    
    elif args.command == 'github-only':
        # Only run GitHub monitoring
        print("📚 Running GitHub monitoring only...")
        companies = finder.github_monitor.run_monitor()
        print(f"Found new internships at: {companies}")
    
    elif args.command == 'linkedin-only':
        # Only run LinkedIn scraping
        if args.companies:
            print(f"🎓 Searching UW alumni at: {', '.join(args.companies)}")
            finder.linkedin_scraper.scrape_companies(args.companies)
        else:
            print("Please specify companies with --companies flag")
    
    elif args.command == 'summary':
        finder.show_summary()
    
    elif args.command == 'recent':
        finder.list_recent_opportunities(args.days)
    
    elif args.command == 'alumni':
        finder.list_uw_alumni(args.company)
    
    elif args.command == 'export':
        finder.export_opportunities_to_csv()
        print(f"Data exported to {finder.config.OUTPUT_CSV}")
    
    elif args.command == 'excel':
        # Update Excel spreadsheet
        print("📊 Updating Excel spreadsheet...")
        success = finder.excel_integration.create_or_update_excel()
        if success:
            print("✅ Excel file updated successfully!")
        else:
            print("❌ Failed to update Excel file")

if __name__ == "__main__":
    main() 