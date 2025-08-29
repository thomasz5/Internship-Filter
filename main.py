#!/usr/bin/env python3
"""
UW Internship Finder - Main Application
Monitors GitHub repos for new internships and finds UW alumni at those companies
"""

import argparse
import sqlite3
import os
import sys
from datetime import datetime
import logging
import time

# Add src folder to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.github_monitor import InternshipGitHubMonitor
from src.linkedin_scraper import UWLinkedInScraper
from src.excel_integration import ExcelIntegration
from src.aws_monitor import EC2Monitor
from src.redis_queue import CompanyQueue

class UWInternshipFinder:
    def __init__(self):
        self.config = Config()
        self.github_monitor = InternshipGitHubMonitor()
        self.linkedin_scraper = UWLinkedInScraper()
        self.excel_integration = ExcelIntegration()
        self.ec2_monitor = EC2Monitor()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_full_cycle(self):
        """Run a complete monitoring cycle"""
        print(f"\nStarting internship monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Monitor GitHub for new internships
        print("\nStep 1: Monitoring GitHub repositories for new internships...")
        new_companies = self.github_monitor.run_monitor()
        
        # Step 2: If new companies found, search for UW alumni
        data_updated = False
        if new_companies:
            print(f"\nStep 2: Searching for UW alumni at {len(set(new_companies))} companies...")
            unique_companies = list(set(new_companies))  # Remove duplicates
            
            # Limit to prevent overwhelming LinkedIn
            if len(unique_companies) > 10:
                print(f"Warning: Limiting search to first 10 companies to be respectful to LinkedIn")
                unique_companies = unique_companies[:10]
            
            self.linkedin_scraper.scrape_companies(unique_companies)
            data_updated = True
        else:
            print("\nNo new internships found, so no LinkedIn scraping needed.")
        
        # Step 3: Update Excel if any new data was found
        if new_companies or data_updated:
            print(f"\nStep 3: Updating Excel spreadsheet...")
            success = self.excel_integration.create_or_update_excel()
            if success:
                # Add notification about new findings
                if new_companies:
                    self.excel_integration.add_notification_to_excel(
                        f"Found {len(new_companies)} new internship opportunities!"
                    )
        
        print(f"\nMonitoring cycle completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def export_opportunities_to_csv(self):
        """Export found opportunities to CSV for easy viewing"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        # Query to join internships with profiles
        query = '''
        SELECT 
            i.company, i.role, i.location, i.application_link, i.discovered_date as internship_date,
            COALESCE(p.name, 'No UW alumnus found') as alumnus_name,
            COALESCE(p.title, '') as alumnus_title,
            COALESCE(p.linkedin_url, '') as alumnus_linkedin
        FROM internships i
        LEFT JOIN profiles p ON LOWER(i.company) = LOWER(p.company)
        ORDER BY i.discovered_date DESC
        '''
        
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            import csv
            with open(self.config.OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Company', 'Role', 'Location', 'Application Link', 'Discovered Date',
                    'UW Alumnus', 'Alumnus Title', 'Alumnus LinkedIn'
                ])
                writer.writerows(rows)
            
            print(f"Exported {len(rows)} opportunities to {self.config.OUTPUT_CSV}")
        else:
            print("No opportunities found to export")
        
        conn.close()
    
    def show_summary(self):
        """Show summary of found data"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        # Get counts
        internship_count = conn.execute("SELECT COUNT(*) FROM internships").fetchone()[0]
        alumni_count = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        
        # Get weekly counts (last 7 days)
        weekly_internships = conn.execute("""
            SELECT COUNT(*) FROM internships 
            WHERE discovered_date >= date('now', '-7 days')
        """).fetchone()[0]
        
        weekly_alumni = conn.execute("""
            SELECT COUNT(*) FROM profiles 
            WHERE discovered_date >= date('now', '-7 days')
        """).fetchone()[0]
        
        # Get top companies by internship count
        top_companies = conn.execute("""
            SELECT company, COUNT(*) as count 
            FROM internships 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 5
        """).fetchall()
        
        conn.close()
        
        print("\nSUMMARY REPORT")
        print("=" * 40)
        print(f"Total Internships Found: {internship_count}")
        print(f"Total UW Alumni Found: {alumni_count}")
        print(f"New This Week: {weekly_internships} internships, {weekly_alumni} alumni")
        
        if top_companies:
            print("Top Companies by Internship Count:")
            for company, count in top_companies:
                print(f"  • {company}: {count} internships")
    
    def show_recent_alumni(self, limit=20, company=None):
        """Show recently found UW alumni"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        if company:
            query = """
                SELECT name, title, company, linkedin_url, discovered_date 
                FROM profiles 
                WHERE LOWER(company) LIKE LOWER(?)
                ORDER BY discovered_date DESC 
                LIMIT ?
            """
            cursor = conn.execute(query, (f"%{company}%", limit))
        else:
            query = """
                SELECT name, title, company, linkedin_url, discovered_date 
                FROM profiles 
                ORDER BY discovered_date DESC 
                LIMIT ?
            """
            cursor = conn.execute(query, (limit,))
        
        alumni = cursor.fetchall()
        conn.close()
        
        if alumni:
            print(f"\nUW Alumni Found{f' at {company}' if company else ' (Most Recent 20)'}:")
            print("-" * 80)
            for i, (name, title, comp, linkedin_url, discovered_date) in enumerate(alumni, 1):
                print(f"{i:2d}. {name}")
                print(f"    Title: {title}")
                print(f"    Company: {comp}")
                print(f"    LinkedIn: {linkedin_url}")
                print(f"    Found: {discovered_date}")
                print()
        else:
            company_text = f" at {company}" if company else ""
            print(f"No UW alumni found{company_text}")
    
    def show_recent_internships(self, limit=20, company=None):
        """Show recently found internships"""
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        if company:
            query = """
                SELECT company, role, location, application_link, discovered_date 
                FROM internships 
                WHERE LOWER(company) LIKE LOWER(?)
                ORDER BY discovered_date DESC 
                LIMIT ?
            """
            cursor = conn.execute(query, (f"%{company}%", limit))
        else:
            query = """
                SELECT company, role, location, application_link, discovered_date 
                FROM internships 
                ORDER BY discovered_date DESC 
                LIMIT ?
            """
            cursor = conn.execute(query, (limit,))
        
        internships = cursor.fetchall()
        conn.close()
        
        if internships:
            company_text = f" at {company}" if company else ""
            print(f"\nRecent Internships{company_text} (Most Recent {min(limit, len(internships))}):")
            print("-" * 80)
            for i, (comp, role, location, app_link, discovered_date) in enumerate(internships, 1):
                print(f"{i:2d}. {comp} - {role}")
                print(f"    Location: {location}")
                if app_link:
                    print(f"    Apply: {app_link}")
                print(f"    Found: {discovered_date}")
                print()
        else:
            company_text = f" at {company}" if company else ""
            print(f"No internships found{company_text}")

def main():
    parser = argparse.ArgumentParser(description='UW Internship Finder - Monitor internships and find UW alumni')
    parser.add_argument('command', choices=[
        'run', 'monitor', 'summary', 'recent', 'alumni', 'export', 'excel', 'github-only', 'linkedin-only', 'aws-status', 'aws-start', 'aws-stop',
        'enqueue', 'worker'
    ], help='Command to execute')
    parser.add_argument('--company', type=str, help='Company name for alumni search')
    parser.add_argument('--days', type=int, default=7, help='Number of days for recent search')
    parser.add_argument('--companies', nargs='+', help='Specific companies to scrape LinkedIn for')
    parser.add_argument('--instance-id', type=str, help='EC2 instance ID for start/stop operations')
    parser.add_argument('--region', type=str, help='AWS region to check (default: all regions)')
    parser.add_argument('--once', action='store_true', help='Worker: process a single job then exit')
    parser.add_argument('--timeout', type=int, default=5, help='Worker: BLPOP timeout seconds')
    
    args = parser.parse_args()
    
    finder = UWInternshipFinder()
    
    if args.command == 'run':
        # Run one complete cycle
        finder.run_full_cycle()
        finder.export_opportunities_to_csv()
        
        # Always update Excel on manual run
        print("\nUpdating Excel spreadsheet...")
        finder.excel_integration.create_or_update_excel()
        
        finder.show_summary()
    
    elif args.command == 'monitor':
        # Start continuous monitoring
        print("Starting continuous monitoring (every 12 hours)")
        print("Press Ctrl+C to stop")
        
        # Schedule the job
        # schedule.every(finder.config.CHECK_INTERVAL_HOURS).hours.do(finder.run_full_cycle) # Removed schedule import
        
        # Run immediately once
        finder.run_full_cycle()
        
        # Then wait for scheduled runs
        try:
            while True:
                # schedule.run_pending() # Removed schedule import
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
    
    elif args.command == 'github-only':
        # Only run GitHub monitoring
        print("Running GitHub monitoring only...")
        companies = finder.github_monitor.run_monitor()
        print(f"Found new internships at: {companies}")
    
    elif args.command == 'linkedin-only':
        # Only run LinkedIn scraping
        if args.companies:
            print(f"Searching UW alumni at: {', '.join(args.companies)}")
            finder.linkedin_scraper.scrape_companies(args.companies)
        else:
            print("Please specify companies with --companies flag")
    
    elif args.command == 'enqueue':
        # Enqueue companies to Redis queue
        queue = CompanyQueue()
        if args.companies:
            enqueued = 0
            for comp in args.companies:
                if queue.enqueue_company(comp):
                    enqueued += 1
            print(f"Enqueued {enqueued}/{len(args.companies)} companies")
        else:
            # If no companies given, enqueue those with recent internships
            companies = finder.github_monitor.get_companies_with_new_internships()
            if not companies:
                print("No recent companies to enqueue. Run github-only first.")
            else:
                enqueued = 0
                for comp in companies:
                    if queue.enqueue_company(comp):
                        enqueued += 1
                print(f"Enqueued {enqueued}/{len(companies)} companies from recent internships")
    
    elif args.command == 'worker':
        # Consume queue and scrape
        queue = CompanyQueue()
        processed = 0
        print("Worker started. Waiting for jobs...")
        try:
            while True:
                company = queue.dequeue_company(block=True, timeout_seconds=args.timeout)
                if not company:
                    if args.once:
                        break
                    continue
                print(f"Processing company: {company}")
                try:
                    finder.linkedin_scraper.scrape_companies([company])
                    processed += 1
                except Exception as e:
                    print(f"Error processing {company}: {e}")
                if args.once:
                    break
        except KeyboardInterrupt:
            print("Worker stopped by user")
        print(f"Processed {processed} companies")
    
    elif args.command == 'summary':
        finder.show_summary()
    
    elif args.command == 'recent':
        finder.show_recent_internships(args.days, args.company)
    
    elif args.command == 'alumni':
        finder.show_recent_alumni(args.days, args.company)
    
    elif args.command == 'export':
        finder.export_opportunities_to_csv()
        print(f"Data exported to {finder.config.OUTPUT_CSV}")
    
    elif args.command == 'excel':
        # Update Excel spreadsheet
        print("Updating Excel spreadsheet...")
        success = finder.excel_integration.create_or_update_excel()
        if success:
            print("Excel file updated successfully!")
        else:
            print("Failed to update Excel file")
    
    elif args.command == 'aws-status':
        # Check AWS EC2 status
        print("Checking AWS EC2 instance status...")
        if args.region:
            status_data = finder.ec2_monitor.check_ec2_instances(args.region)
        else:
            status_data = finder.ec2_monitor.check_all_regions()
        
        finder.ec2_monitor.print_status_report(status_data)
        
        # Also update Excel with this information
        print("\nUpdating Excel with AWS status...")
        finder.excel_integration.create_or_update_excel()
    
    elif args.command == 'aws-start':
        # Start EC2 instance
        if not args.instance_id:
            print("❌ Please specify --instance-id for instance to start")
            sys.exit(1)
        
        print(f"Starting EC2 instance {args.instance_id}...")
        result = finder.ec2_monitor.start_instance(args.instance_id, args.region)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ {result['message']}")
            # Update Excel after instance state change
            finder.excel_integration.create_or_update_excel()
    
    elif args.command == 'aws-stop':
        # Stop EC2 instance
        if not args.instance_id:
            print("❌ Please specify --instance-id for instance to stop")
            sys.exit(1)
        
        print(f"Stopping EC2 instance {args.instance_id}...")
        result = finder.ec2_monitor.stop_instance(args.instance_id, args.region)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ {result['message']}")
            # Update Excel after instance state change
            finder.excel_integration.create_or_update_excel()

if __name__ == "__main__":
    main() 