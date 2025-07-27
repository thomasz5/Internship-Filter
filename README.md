# UW Internship Finder 🎓

**Find internship opportunities and connect with University of Washington alumni!**

This tool automatically monitors the [SimplifyJobs Summer 2026 Internships](https://github.com/SimplifyJobs/Summer2026-Internships.git) repository and other internship tracking repos for new opportunities, then helps you find UW alumni working at those companies.

## ⚡ What This Tool Does

1. **🔍 Monitors GitHub** - Tracks internship repositories for new postings every 12 hours
2. **🎓 Finds UW Alumni** - Searches LinkedIn for University of Washington graduates at companies with new internships
3. **📊 Organizes Data** - Stores everything in a database and exports to CSV for easy viewing
4. **🤖 Works Automatically** - Runs in the background so you don't have to manually check

## 🚨 Important Legal Notice

**This tool is for personal educational use by students.** 
- Only scrapes publicly available information
- Uses conservative rate limiting to respect LinkedIn's servers
- You are responsible for complying with LinkedIn's Terms of Service
- Consider using LinkedIn's official APIs for commercial use

## 🚀 Quick Setup

### Prerequisites
- Python 3.9+
- Google Chrome browser
- LinkedIn account

### Installation

1. **Clone and setup**
```bash
git clone <repository-url>
cd uw-internship-finder
python setup.py
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
python main.py run

# Start continuous monitoring (every 12 hours)
python main.py monitor
```

That's it! The tool will now automatically find new internships and UW alumni for you.

## 📋 Usage Commands

### Main Commands

```bash
# Run a complete cycle (check GitHub + LinkedIn scraping)
python main.py run

# Start continuous monitoring every 12 hours
python main.py monitor

# Show summary of what you've found
python main.py summary

# View recent internship opportunities
python main.py recent --days 7

# Export everything to CSV for easy viewing
python main.py export
```

### Specific Tasks

```bash
# Only check GitHub for new internships
python main.py github-only

# Only search LinkedIn for UW alumni at specific companies
python main.py linkedin-only --companies "Microsoft" "Amazon" "Google"

# View UW alumni found at a specific company
python main.py alumni --company Microsoft

# See recent opportunities from last 14 days
python main.py recent --days 14
```

### Example Output

When you run `python main.py run`, you'll see:

```
🔍 Starting internship monitoring cycle at 2024-01-15 14:30:00
============================================================

📚 Step 1: Monitoring GitHub repositories for new internships...
🎉 Found 5 new internship opportunities!
• Amazon - Software Development Engineer Intern
• Microsoft - Data Science Intern  
• Google - Product Manager Intern
• ... and 2 more!

🎓 Step 2: Searching for UW alumni at 3 companies...
✅ Found 8 UW alumni at Amazon
   • John Smith - Senior Software Engineer
   • Sarah Johnson - Product Manager
   • Mike Chen - Data Scientist
❌ No UW alumni found at Microsoft
✅ Found 12 UW alumni at Google
   • Emily Davis - Software Engineer
   • David Kim - UX Designer
   • ... and 10 more

🎓 Total: Found 20 UW alumni across all companies!
📊 Exported 25 opportunities to found_opportunities.csv
```

## 💡 How It Works

### Step 1: GitHub Monitoring
- Tracks the [SimplifyJobs Summer 2026 Internships](https://github.com/SimplifyJobs/Summer2026-Internships.git) repository
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
- Creates CSV exports for easy viewing in Excel/Sheets
- Tracks when each internship and profile was discovered
- Provides summary statistics and recent activity reports

## 📊 What You Get

The tool creates several outputs to help with your internship search:

1. **Database** (`internship_tracker.db`) - All data stored locally
2. **CSV Export** (`found_opportunities.csv`) - Spreadsheet with internships + alumni
3. **Console Output** - Real-time updates and summaries
4. **Log File** (`scraper.log`) - Detailed activity logs

## 🔧 Troubleshooting

### Common Issues

**Chrome not found**
- Install Google Chrome from [chrome.google.com](https://www.google.com/chrome/)
- Make sure it's in your Applications folder (Mac) or Program Files (Windows)

**LinkedIn login fails**
- Double-check your email/password in `.env`
- Try logging in manually to check if LinkedIn requires verification
- If LinkedIn shows a captcha, complete it manually and try again

**No new internships found**
- The tool only finds truly new postings since the last check
- Internship repos are updated most frequently during recruiting season
- Try `python main.py github-only` to test the GitHub monitoring

**LinkedIn search finds no alumni**  
- Some companies may not have many UW alumni
- Try searching manually on LinkedIn to verify
- The tool uses conservative search terms to avoid false positives

## 💡 Tips for Best Results

1. **Run during peak recruiting season** (September-December, January-March)
2. **Check the CSV export** regularly - it's the easiest way to review findings  
3. **Start with continuous monitoring** (`python main.py monitor`) to catch opportunities early
4. **Use the alumni connections** - reach out to UW graduates for informational interviews
5. **Be respectful** - don't run the tool excessively to avoid LinkedIn rate limits

## 🎯 What's Next?

After finding opportunities and alumni:

1. **Research the companies** - Learn about their culture, recent news, products
2. **Customize your applications** - Tailor your resume/cover letter for each role  
3. **Reach out to alumni** - Send thoughtful LinkedIn messages mentioning your UW connection
4. **Apply early** - New postings often get hundreds of applications quickly
5. **Follow up** - Keep track of your applications and send follow-up notes

## 📚 Additional Resources

- [SimplifyJobs Internship Repo](https://github.com/SimplifyJobs/Summer2026-Internships.git) - The main source we monitor
- [UW Career Center](https://careers.uw.edu/) - Your campus career services
- [Simplify](https://simplify.jobs/) - Tools for auto-filling applications
- [LinkedIn Alumni Tool](https://www.linkedin.com/school/university-of-washington/people/) - Manual alumni search

---

**Made for UW students by a fellow student** 🤖  
*Use responsibly and good luck with your internship search!* 