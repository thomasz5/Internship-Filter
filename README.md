# UW Internship Finder 🎓

**Find internship opportunities and connect with University of Washington alumni!**

This tool automatically monitors the [SimplifyJobs Summer 2026 Internships](https://github.com/SimplifyJobs/Summer2026-Internships.git) repository and other internship tracking repos for new opportunities, then helps you find UW alumni working at those companies.

## Important Legal Notice

**This tool is for personal educational use by students.** 
- Only scrapes publicly available information
- Uses conservative rate limiting to respect LinkedIn's servers
- You are responsible for complying with LinkedIn's Terms of Service
- Consider using LinkedIn's official APIs for commercial use


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

## Usage Commands

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






**Made for UW students by a fellow student** 
*Use responsibly and good luck with your internship search!* 
