#!/usr/bin/env python3
"""
Sync Data from EC2 Script
Downloads latest findings from EC2 instance to local environment
"""

import subprocess
import os
import sys
from datetime import datetime

def run_command(command, description):
    """Run a shell command and return success status"""
    print(f"📥 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def sync_from_ec2():
    """Download all data from EC2 instance"""
    print("📡 Syncing Data from EC2")
    print("=" * 40)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # EC2 connection details
    ec2_host = "98.83.120.149"
    key_file = "~/Downloads/thomacide.pem"
    remote_path = "/home/ubuntu/Internship-Filter"
    
    print(f"🔗 Connecting to EC2: {ec2_host}")
    print(f"📁 Remote path: {remote_path}")
    print()
    
    # Files to download
    files_to_sync = [
        ("internship_tracker.db", "Database with all internships and alumni"),
        ("UW_Internship_Tracker.xlsx", "Excel spreadsheet with formatted results"),
        ("found_opportunities.csv", "CSV export for easy viewing"),
        ("scraper.log", "Application logs"),
        (".env", "Environment configuration"),
    ]
    
    success_count = 0
    
    for filename, description in files_to_sync:
        command = f"scp -i {key_file} ubuntu@{ec2_host}:{remote_path}/{filename} ."
        if run_command(command, f"Downloading {filename} ({description})"):
            success_count += 1
    
    print(f"\n📊 Sync Summary")
    print("=" * 20)
    print(f"✅ Successfully synced: {success_count}/{len(files_to_sync)} files")
    
    if success_count > 0:
        print(f"\n📁 Downloaded files:")
        for filename, _ in files_to_sync[:success_count]:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"  • {filename} ({size:,} bytes)")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return success_count == len(files_to_sync)

def check_ec2_status():
    """Check the status of the EC2 service"""
    print("\n🔍 Checking EC2 Service Status")
    print("=" * 35)
    
    ec2_host = "98.83.120.149"
    key_file = "~/Downloads/thomacide.pem"
    
    status_commands = [
        ("sudo systemctl status uw-internship-finder --no-pager -l | head -5", "Service status"),
        ("python3 main.py summary", "Latest findings summary"),
        ("tail -5 scraper.log", "Recent log entries"),
    ]
    
    for command, description in status_commands:
        print(f"\n📋 {description}:")
        ssh_command = f"ssh -i {key_file} ubuntu@{ec2_host} 'cd Internship-Filter && {command}'"
        result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Clean up the output
            output = result.stdout.strip()
            for line in output.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"  ❌ Failed to get {description.lower()}")

def show_local_summary():
    """Show summary of local data after sync"""
    print("\n📊 Local Data Summary")
    print("=" * 25)
    
    try:
        import sqlite3
        
        if os.path.exists("internship_tracker.db"):
            conn = sqlite3.connect("internship_tracker.db")
            
            # Get counts
            internship_count = conn.execute('SELECT COUNT(*) FROM internships').fetchone()[0]
            profile_count = conn.execute('SELECT COUNT(*) FROM profiles').fetchone()[0]
            
            print(f"📈 Database contents:")
            print(f"  • Total internships: {internship_count}")
            print(f"  • UW alumni found: {profile_count}")
            
            # Recent internships
            recent = conn.execute('''
                SELECT company, COUNT(*) as count 
                FROM internships 
                GROUP BY company 
                ORDER BY count DESC 
                LIMIT 3
            ''').fetchall()
            
            if recent:
                print(f"\n🏆 Top companies by internship count:")
                for company, count in recent:
                    print(f"  • {company}: {count} internships")
            
            conn.close()
            
        if os.path.exists("UW_Internship_Tracker.xlsx"):
            size = os.path.getsize("UW_Internship_Tracker.xlsx")
            print(f"\n📄 Excel file: UW_Internship_Tracker.xlsx ({size:,} bytes)")
            
        if os.path.exists("found_opportunities.csv"):
            with open("found_opportunities.csv", 'r') as f:
                lines = len(f.readlines()) - 1  # Subtract header
            print(f"📄 CSV file: {lines} opportunities")
            
    except Exception as e:
        print(f"❌ Error reading local data: {e}")

def main():
    """Main sync function"""
    print("🔄 EC2 Data Sync Tool")
    print("=" * 50)
    
    # Check if key file exists
    key_file = os.path.expanduser("~/Downloads/thomacide.pem")
    if not os.path.exists(key_file):
        print(f"❌ SSH key not found: {key_file}")
        print("Please ensure your EC2 key file is in ~/Downloads/")
        sys.exit(1)
    
    # Sync data from EC2
    sync_success = sync_from_ec2()
    
    # Check EC2 status
    check_ec2_status()
    
    # Show local summary
    if sync_success:
        show_local_summary()
    
    print(f"\n🎯 Next steps:")
    print(f"  • Run: python3 test_local.py (test everything locally)")
    print(f"  • Run: python3 main.py summary (view findings)")
    print(f"  • Setup LinkedIn: python3 setup_linkedin_session.py")

if __name__ == "__main__":
    main() 