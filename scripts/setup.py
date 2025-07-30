#!/usr/bin/env python3
"""
Setup script for UW Internship Finder
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error installing requirements")
        return False
    return True

def setup_environment():
    """Create environment file if it doesn't exist"""
    env_file = ".env"
    env_example = """# UW Internship Finder Configuration

# LinkedIn Credentials (required for scraping)
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password

# GitHub Token (optional but recommended for higher rate limits)
# Get from: https://github.com/settings/tokens
GITHUB_TOKEN=your-github-token

# You can modify these in config.py if needed
"""
    
    if not os.path.exists(env_file):
        print("📝 Creating environment file...")
        with open(env_file, 'w') as f:
            f.write(env_example)
        print(f"✅ Created {env_file} - please edit it with your credentials!")
        return True
    else:
        print(f"⚠️  {env_file} already exists - skipping creation")
        return False

def check_chrome():
    """Check if Chrome is installed"""
    print("🔍 Checking for Chrome browser...")
    
    # Common Chrome paths
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium-browser",  # Ubuntu/Debian
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",  # Windows 32-bit
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_found = True
            break
    
    if chrome_found:
        print("✅ Chrome browser found!")
    else:
        print("⚠️  Chrome browser not found in common locations.")
        print("   Please install Chrome from: https://www.google.com/chrome/")
    
    return chrome_found

def main():
    print("🎓 UW Internship Finder Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        print("Setup failed!")
        return
    
    # Check Chrome
    check_chrome()
    
    # Setup environment
    env_created = setup_environment()
    
    print("\n🚀 Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your LinkedIn credentials")
    
    if env_created:
        print("2. Test the GitHub monitor: python main.py github-only")
        print("3. Test LinkedIn scraping: python main.py linkedin-only --companies Microsoft")
        print("4. Run full monitoring: python main.py run")
        print("5. Start continuous monitoring: python main.py monitor")
    else:
        print("2. Run: python main.py run")
    
    print("\nFor help: python main.py --help")

if __name__ == "__main__":
    main() 