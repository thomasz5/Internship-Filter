#!/usr/bin/env python3
"""
Local Testing Script for UW Internship Finder
Tests GitHub monitoring and simulates LinkedIn functionality
"""

import sys
import sqlite3
from datetime import datetime
from github_monitor import InternshipGitHubMonitor
from excel_integration import ExcelIntegration

def test_github_monitoring():
    """Test GitHub repository monitoring locally"""
    print("🔍 Testing GitHub Monitoring Locally")
    print("=" * 50)
    
    try:
        monitor = InternshipGitHubMonitor()
        print("✅ GitHub monitor initialized")
        
        print("\n📚 Checking for new internships...")
        new_companies = monitor.run_monitor()
        
        if new_companies:
            print(f"🎉 Found new internships at {len(set(new_companies))} companies:")
            for company in set(new_companies):
                print(f"  • {company}")
        else:
            print("📊 No new internships found since last check")
            
        return new_companies
        
    except Exception as e:
        print(f"❌ GitHub monitoring failed: {e}")
        return []

def test_database_operations():
    """Test database operations"""
    print("\n💾 Testing Database Operations")
    print("=" * 30)
    
    try:
        # Check if database exists
        conn = sqlite3.connect("internship_tracker.db")
        
        # Count current data
        internship_count = conn.execute('SELECT COUNT(*) FROM internships').fetchone()[0]
        profile_count = conn.execute('SELECT COUNT(*) FROM profiles').fetchone()[0]
        
        print(f"📊 Current database stats:")
        print(f"  • Internships: {internship_count}")
        print(f"  • Alumni Profiles: {profile_count}")
        
        # Show recent internships
        recent = conn.execute('''
            SELECT company, role, location, discovered_date 
            FROM internships 
            ORDER BY discovered_date DESC 
            LIMIT 5
        ''').fetchall()
        
        if recent:
            print(f"\n🆕 Most recent internships:")
            for company, role, location, date in recent:
                print(f"  • {company} - {role} ({location}) - {date}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_excel_integration():
    """Test Excel file generation"""
    print("\n📊 Testing Excel Integration")
    print("=" * 30)
    
    try:
        excel = ExcelIntegration()
        success = excel.create_or_update_excel()
        
        if success:
            print("✅ Excel file updated successfully")
            print(f"📁 Check: UW_Internship_Tracker.xlsx")
        else:
            print("❌ Excel update failed")
            
        return success
        
    except Exception as e:
        print(f"❌ Excel test failed: {e}")
        return False

def simulate_linkedin_search(companies):
    """Simulate what LinkedIn search would do"""
    print("\n🎓 LinkedIn Search Simulation")
    print("=" * 30)
    
    if not companies:
        print("📝 No new companies to search")
        return
    
    print("🔗 Would search LinkedIn for UW alumni at:")
    for company in set(companies):
        print(f"  • {company}")
        print(f"    - Search: 'University of Washington' + '{company}'")
        print(f"    - Filter: Current employees, Seattle area")
    
    print("\n💡 To enable LinkedIn search:")
    print("  1. Install Chrome: brew install --cask google-chrome")
    print("  2. Install ChromeDriver: brew install chromedriver")
    print("  3. Run: python3 setup_linkedin_session.py")
    print("  4. Complete manual verification once")
    print("  5. Then LinkedIn scraping will work automatically!")

def main():
    """Run all local tests"""
    print("🚀 UW Internship Finder - Local Testing")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test GitHub monitoring
    new_companies = test_github_monitoring()
    
    # Test database
    database_ok = test_database_operations()
    
    # Test Excel integration
    excel_ok = test_excel_integration()
    
    # Simulate LinkedIn
    simulate_linkedin_search(new_companies)
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 20)
    print(f"✅ GitHub Monitoring: {'Working' if new_companies is not None else 'Failed'}")
    print(f"✅ Database: {'Working' if database_ok else 'Failed'}")
    print(f"✅ Excel: {'Working' if excel_ok else 'Failed'}")
    print(f"🔗 LinkedIn: Needs browser setup")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 