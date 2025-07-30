#!/usr/bin/env python3
"""
LinkedIn Session Setup Script
Run this once to manually complete LinkedIn login and save session
"""

import sys
from linkedin_scraper import UWLinkedInScraper

def setup_linkedin_session():
    """Setup LinkedIn session with manual verification"""
    print("🔐 LinkedIn Session Setup")
    print("=" * 50)
    print("This script will:")
    print("1. Open LinkedIn in a browser window")
    print("2. Let you manually complete login and any security challenges")
    print("3. Save your session for future automated use")
    print("4. After this, LinkedIn scraping will work headlessly")
    print()
    
    input("Press Enter to continue...")
    
    scraper = UWLinkedInScraper()
    
    try:
        print("\n🌐 Opening browser...")
        # Force non-headless mode for initial setup
        scraper.setup_driver(headless=False)
        
        print("🔑 Attempting LinkedIn login...")
        if scraper.login():
            print("✅ LinkedIn session established and saved!")
            print("✅ Future runs will use this session automatically")
            
            # Test the session by trying to access profile
            print("\n🧪 Testing session...")
            scraper.driver.get("https://www.linkedin.com/feed/")
            if "feed" in scraper.driver.current_url:
                print("✅ Session test successful!")
            
        else:
            print("❌ Failed to establish LinkedIn session")
            return False
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False
    finally:
        scraper.cleanup()
    
    print("\n🎉 Setup complete!")
    print("You can now run the LinkedIn scraper headlessly with:")
    print("  python3 main.py linkedin-only --companies 'Apple' 'Microsoft'")
    return True

if __name__ == "__main__":
    success = setup_linkedin_session()
    sys.exit(0 if success else 1) 