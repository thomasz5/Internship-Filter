# UW Internship Finder

**Find internship opportunities and connect with University of Washington alumni.**

This tool automatically monitors internship tracking repositories for new opportunities and helps you find UW alumni working at those companies.

## What This Tool Does

1. **Monitors GitHub** - Tracks internship repositories for new postings every 6 hours
2. **Finds UW Alumni** - Searches LinkedIn for University of Washington graduates at companies with new internships
3. **Organizes Data** - Stores everything in a database and exports to Excel/CSV for easy viewing
4. **Works Automatically** - Runs in the background without manual checking

## Important Legal Notice

**This tool is for personal educational use by students.**
- Only scrapes publicly available information
- Uses conservative rate limiting to respect LinkedIn's servers
- You are responsible for complying with LinkedIn's Terms of Service
- Consider using LinkedIn's official APIs for commercial use

## Quick Setup

### Prerequisites
- Python 3.9+
- Google Chrome browser
- LinkedIn account

### Installation

1. **Clone and setup**
```bash
git clone <repository-url>
cd uw-internship-finder
python3 scripts/setup.py
```

2. **Configure your credentials**
Edit the `.env` file that was created:
```bash
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
```

3. **Start monitoring**
```bash
# Run once to test
python3 main.py run

# Start continuous monitoring (every 12 hours)
python3 main.py monitor
```

## Usage Commands

### Main Commands

```bash
# Run a complete cycle (check GitHub + LinkedIn scraping)
python3 main.py run

# Start continuous monitoring every 12 hours
python3 main.py monitor

# Show summary of findings
python3 main.py summary

# Update Excel spreadsheet
python3 main.py excel

# View recent internship opportunities
python3 main.py recent --days 7
```

### Specific Tasks

```bash
# Only check GitHub for new internships
python3 main.py github-only

# Only search LinkedIn for UW alumni at specific companies
python3 main.py linkedin-only --companies "Microsoft" "Amazon" "Google"

# View UW alumni found at a specific company
python3 main.py alumni --company Microsoft

# See recent opportunities from last 14 days
python3 main.py recent --days 14

# Export to CSV
python3 main.py export
```

### Example Output

When you run `python3 main.py run`, you'll see:

```
Starting internship monitoring cycle at 2024-01-15 14:30:00
============================================================

Step 1: Monitoring GitHub repositories for new internships...
Found 5 new internship opportunities!
• Amazon - Software Development Engineer Intern
• Microsoft - Data Science Intern  
• Google - Product Manager Intern
• ... and 2 more!

Step 2: Searching for UW alumni at 3 companies...
Found 8 UW alumni at Amazon
   • John Smith - Senior Software Engineer
   • Sarah Johnson - Product Manager
   • Mike Chen - Data Scientist
No UW alumni found at Microsoft
Found 12 UW alumni at Google
   • Emily Davis - Software Engineer
   • David Kim - UX Designer
   • ... and 10 more

Total: Found 20 UW alumni across all companies!
Exported 25 opportunities to found_opportunities.csv
```

## How It Works

### Step 1: GitHub Monitoring
- Tracks the SimplifyJobs Summer 2026 Internships repository and other internship repos
- Detects when new internship postings are added (usually daily)
- Focuses on Seattle-area, remote, and US-based positions
- Filters for internship keywords like "intern", "co-op", "summer", etc.

### Step 2: LinkedIn Alumni Search  
- For each company with new internships, searches LinkedIn for UW alumni
- Uses search terms like: `school:"University of Washington" AND company:"Microsoft"`
- Extracts basic info: name, current title, company
- Limits to ~20 profiles per company to be respectful

### Step 3: Data Organization
- Stores everything in a local SQLite database
- Creates Excel and CSV exports for easy viewing
- Tracks when each internship and profile was discovered
- Provides summary statistics and recent activity reports

## What You Get

The tool creates several outputs to help with your internship search:

1. **Database** (`internship_tracker.db`) - All data stored locally
2. **Excel Spreadsheet** (`UW_Internship_Tracker.xlsx`) - Formatted with multiple sheets
3. **CSV Export** (`found_opportunities.csv`) - Simple spreadsheet format
4. **Console Output** - Real-time updates and summaries
5. **Log File** (`scraper.log`) - Detailed activity logs

## EC2 Deployment

For continuous monitoring, you can deploy this on AWS EC2:

### Local EC2 Commands
```bash
# Sync data from EC2 to local
python3 scripts/sync_from_ec2.py

# Check EC2 status remotely
ssh -i ~/Downloads/your-key.pem ubuntu@your-ec2-ip "cd Internship-Filter && python3 main.py summary"

# Update code on EC2
ssh -i ~/Downloads/your-key.pem ubuntu@your-ec2-ip "cd Internship-Filter && git pull && sudo systemctl restart uw-internship-finder"
```

### EC2 Service Management
```bash
# Check service status
sudo systemctl status uw-internship-finder

# View logs
sudo journalctl -u uw-internship-finder -f

# Restart service
sudo systemctl restart uw-internship-finder

# Run manually for testing
python3 main.py run
```

## Troubleshooting

### Common Issues

**Chrome not found**
- Install Google Chrome from chrome.google.com
- Make sure it's in your Applications folder (Mac) or Program Files (Windows)

**LinkedIn login fails**
- Double-check your email/password in `.env`
- Try logging in manually to check if LinkedIn requires verification
- If LinkedIn shows a captcha, complete it manually and try again

**No new internships found**
- The tool only finds truly new postings since the last check
- Internship repos are updated most frequently during recruiting season
- Try `python3 main.py github-only` to test the GitHub monitoring

**LinkedIn search finds no alumni**  
- Some companies may not have many UW alumni
- Try searching manually on LinkedIn to verify
- The tool uses conservative search terms to avoid false positives

**Made for UW students. Use responsibly and good luck with your internship search.** 