# UW Internship Finder

**Find internship opportunities and connect with University of Washington alumni.**

This tool automatically monitors internship tracking repositories for new opportunities and helps you find UW alumni working at those companies.

## Demo Video

[![Recruitment Demo](./Recruitment.mp4)](./Recruitment.mp4)

## What This Tool Does

1. **Monitors GitHub** - Tracks internship repositories for new postings every 12 hours
2. **Finds UW Alumni** - Searches LinkedIn for University of Washington graduates at companies with new internships
3. **Organizes Data** - Stores everything in a database and exports to CSV for easy viewing
4. **Works Automatically** - Runs in the background so you don't have to manually check

## Important Legal Notice

**This tool is for personal educational use by students.**
- Only scrapes publicly available information
- Uses conservative rate limiting to respect LinkedIn's servers
- You are responsible for complying with LinkedIn's Terms of Service


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

# Show summary of finding
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



**Made for UW students by a fellow student**   
