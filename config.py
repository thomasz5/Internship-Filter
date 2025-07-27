# Student LinkedIn Scraper Configuration

import os
from typing import List

class Config:
    # LinkedIn Authentication
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', '')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', '')
    
    # Target Settings
    TARGET_COLLEGE = "University of Washington"
    TARGET_LOCATION = "Seattle"
    PREFERRED_LOCATIONS = ["Seattle", "Bellevue", "Redmond", "Remote", "United States"]
    
    # GitHub Repositories to Monitor
    GITHUB_REPOS = [
        "https://github.com/SimplifyJobs/Summer2026-Internships.git",
        "https://github.com/speedyapply/2026-SWE-College-Jobs.git"
    ]
    
    # Monitoring Settings
    CHECK_INTERVAL_HOURS = 6
    MAX_PROFILES_PER_COMPANY = 20  # Reasonable limit
    
    # LinkedIn Scraping Settings
    REQUEST_DELAY_MIN = 3.0  # Conservative delays for personal use
    REQUEST_DELAY_MAX = 6.0
    MAX_PAGES_PER_SEARCH = 5
    
    # Role Matching Keywords
    INTERNSHIP_KEYWORDS = [
        'intern', 'internship', 'summer intern', 'co-op', 'coop',
        'student', 'new grad', 'entry level', 'software engineer intern',
        'data science intern', 'product manager intern'
    ]
    
    # Seattle Area Companies (to prioritize)
    SEATTLE_COMPANIES = [
        'Amazon', 'Microsoft', 'Boeing', 'Expedia', 'Zillow',
        'Starbucks', 'Nintendo', 'T-Mobile', 'Alaska Airlines',
        'Costco', 'Nordstrom', 'REI', 'Weyerhaeuser'
    ]
    
    # Database
    DATABASE_PATH = "internship_tracker.db"
    
    # Output Settings
    OUTPUT_CSV = "found_opportunities.csv"
    LOG_FILE = "scraper.log" 