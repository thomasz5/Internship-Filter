# LinkedIn Profile Scraper - Implementation Guide

## Project Structure

```
linkedin-scraper/
├── src/
│   ├── __init__.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── linkedin_scraper.py
│   │   ├── github_monitor.py
│   │   └── anti_detection.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── profile.py
│   │   ├── education.py
│   │   └── job_posting.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── migrations/
│   │   └── models.py
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── education_filter.py
│   │   ├── company_filter.py
│   │   └── role_matcher.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── helpers.py
│   └── api/
│       ├── __init__.py
│       ├── routes.py
│       └── schemas.py
├── tests/
├── config/
│   ├── settings.py
│   └── logging.yaml
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

## Prerequisites & Setup

### System Requirements
```bash
# Python 3.9+
python --version

# Chrome/Chromium browser
# Docker (optional but recommended)
# PostgreSQL (or SQLite for development)
```

### Environment Setup

1. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Variables**
```bash
cp .env.example .env
# Edit .env with your configurations
```

## Core Implementation

### 1. Requirements File

```python
# requirements.txt
selenium==4.15.0
beautifulsoup4==4.12.2
requests==2.31.0
sqlalchemy==2.0.23
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0
celery==5.3.4
redis==5.0.1
psycopg2-binary==2.9.9
playwright==1.40.0
fake-useragent==1.4.0
python-dateutil==2.8.2
fuzzywuzzy==0.18.0
python-levenshtein==0.23.0
pandas==2.1.3
numpy==1.25.2
aiohttp==3.9.1
python-multipart==0.0.6
Jinja2==3.1.2
pytest==7.4.3
python-github==1.59.1
```

### 2. Configuration Management

```python
# config/settings.py
import os
from typing import Optional, List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./linkedin_scraper.db"
    
    # LinkedIn
    LINKEDIN_EMAIL: Optional[str] = None
    LINKEDIN_PASSWORD: Optional[str] = None
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    
    # Scraping Settings
    MAX_CONCURRENT_REQUESTS: int = 3
    REQUEST_DELAY_MIN: float = 2.0
    REQUEST_DELAY_MAX: float = 5.0
    
    # Anti-Detection
    USE_PROXY: bool = False
    PROXY_LIST: List[str] = []
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    # Filters
    TARGET_COLLEGES: List[str] = []
    TARGET_COMPANIES: List[str] = []
    TARGET_ROLES: List[str] = []
    
    # Monitoring
    GITHUB_REPOS_TO_MONITOR: List[str] = []
    CHECK_INTERVAL_HOURS: int = 24
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3. Database Models

```python
# src/models/profile.py
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional

Base = declarative_base()

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    headline = Column(Text)
    current_company = Column(String)
    current_role = Column(String)
    location = Column(String)
    linkedin_url = Column(String, unique=True)
    connections_count = Column(Integer)
    profile_image_url = Column(String)
    summary = Column(Text)
    skills = Column(JSON)  # List of skills
    languages = Column(JSON)  # List of languages
    last_scraped = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    education = relationship("Education", back_populates="profile")
    experience = relationship("Experience", back_populates="profile")
    contact_info = relationship("ContactInfo", back_populates="profile", uselist=False)

class Education(Base):
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("profiles.id"))
    institution = Column(String, nullable=False)
    degree = Column(String)
    field_of_study = Column(String)
    start_year = Column(Integer)
    end_year = Column(Integer)
    grade = Column(String)
    activities = Column(JSON)
    description = Column(Text)
    
    profile = relationship("Profile", back_populates="education")

class Experience(Base):
    __tablename__ = "experience"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("profiles.id"))
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String)
    start_date = Column(String)  # LinkedIn often shows "Month Year"
    end_date = Column(String)
    is_current = Column(Boolean, default=False)
    description = Column(Text)
    
    profile = relationship("Profile", back_populates="experience")

class ContactInfo(Base):
    __tablename__ = "contact_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, ForeignKey("profiles.id"))
    email = Column(String)
    phone = Column(String)
    website = Column(String)
    twitter = Column(String)
    
    profile = relationship("Profile", back_populates="contact_info")

class JobPosting(Base):
    __tablename__ = "job_postings"
    
    id = Column(String, primary_key=True)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    requirements = Column(JSON)
    location = Column(String)
    employment_type = Column(String)  # Internship, Full-time, etc.
    posted_date = Column(DateTime)
    github_repo = Column(String)
    commit_hash = Column(String)
    raw_content = Column(Text)
    keywords = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 4. LinkedIn Scraper Implementation

```python
# src/scrapers/linkedin_scraper.py
import time
import random
import json
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from ..models.profile import Profile, Education, Experience, ContactInfo
from ..utils.config import settings
from .anti_detection import AntiDetectionMixin

class LinkedInScraper(AntiDetectionMixin):
    def __init__(self):
        self.driver = None
        self.wait = None
        self.session_active = False
        
    def setup_driver(self):
        """Initialize Chrome driver with anti-detection measures"""
        options = Options()
        
        # Anti-detection options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        ua = UserAgent()
        options.add_argument(f'--user-agent={ua.random}')
        
        # Proxy support
        if settings.USE_PROXY and settings.PROXY_LIST:
            proxy = random.choice(settings.PROXY_LIST)
            options.add_argument(f'--proxy-server={proxy}')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
    def login(self, email: str, password: str) -> bool:
        """Login to LinkedIn"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait and fill email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            self.simulate_typing(email_field, email)
            
            # Fill password
            password_field = self.driver.find_element(By.ID, "password")
            self.simulate_typing(password_field, password)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Check if login successful
            self.wait.until(lambda driver: "feed" in driver.current_url or "challenge" in driver.current_url)
            
            if "challenge" in self.driver.current_url:
                print("LinkedIn challenge detected. Manual intervention required.")
                input("Please complete the challenge and press Enter to continue...")
            
            self.session_active = True
            return True
            
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def search_profiles(self, search_criteria: Dict) -> List[str]:
        """Search for profiles based on criteria"""
        profile_urls = []
        
        try:
            # Build search URL
            search_url = self._build_search_url(search_criteria)
            self.driver.get(search_url)
            
            # Handle pagination
            page = 1
            max_pages = search_criteria.get('max_pages', 5)
            
            while page <= max_pages:
                print(f"Scraping page {page}")
                
                # Wait for results to load
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-result__wrapper")))
                
                # Extract profile URLs from current page
                page_urls = self._extract_profile_urls_from_page()
                profile_urls.extend(page_urls)
                
                # Go to next page
                if not self._go_to_next_page():
                    break
                    
                page += 1
                self.random_delay()
            
            print(f"Found {len(profile_urls)} profiles")
            return profile_urls
            
        except Exception as e:
            print(f"Search failed: {e}")
            return profile_urls
    
    def scrape_profile(self, profile_url: str) -> Optional[Dict]:
        """Scrape individual profile data"""
        try:
            self.driver.get(profile_url)
            self.random_delay()
            
            # Wait for profile to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pv-text-details__left-panel")))
            
            # Scroll to load all sections
            self._scroll_to_load_sections()
            
            # Extract data
            profile_data = {
                'linkedin_url': profile_url,
                'name': self._extract_name(),
                'headline': self._extract_headline(),
                'location': self._extract_location(),
                'current_company': self._extract_current_company(),
                'current_role': self._extract_current_role(),
                'summary': self._extract_summary(),
                'education': self._extract_education(),
                'experience': self._extract_experience(),
                'skills': self._extract_skills(),
                'contact_info': self._extract_contact_info()
            }
            
            return profile_data
            
        except Exception as e:
            print(f"Failed to scrape profile {profile_url}: {e}")
            return None
    
    def _build_search_url(self, criteria: Dict) -> str:
        """Build LinkedIn search URL with filters"""
        base_url = "https://www.linkedin.com/search/results/people/?"
        params = []
        
        # Keywords
        if criteria.get('keywords'):
            params.append(f"keywords={criteria['keywords']}")
        
        # Current company
        if criteria.get('current_company'):
            params.append(f"currentCompany=%5B%22{criteria['current_company']}%22%5D")
        
        # School
        if criteria.get('school'):
            params.append(f"school=%5B%22{criteria['school']}%22%5D")
        
        # Location
        if criteria.get('location'):
            params.append(f"geoUrn=%5B%22{criteria['location']}%22%5D")
        
        return base_url + "&".join(params)
    
    def _extract_profile_urls_from_page(self) -> List[str]:
        """Extract profile URLs from search results page"""
        urls = []
        try:
            # Find all profile links
            profile_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
            
            for link in profile_links:
                href = link.get_attribute('href')
                if '/in/' in href and '?' not in href:  # Clean profile URLs only
                    urls.append(href)
            
            # Remove duplicates
            return list(set(urls))
            
        except Exception as e:
            print(f"Error extracting profile URLs: {e}")
            return urls
    
    def _extract_name(self) -> str:
        """Extract profile name"""
        try:
            name_element = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'text-heading-xlarge')]")
            return name_element.text.strip()
        except:
            return ""
    
    def _extract_headline(self) -> str:
        """Extract profile headline"""
        try:
            headline_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'text-body-medium')]")
            return headline_element.text.strip()
        except:
            return ""
    
    def _extract_location(self) -> str:
        """Extract profile location"""
        try:
            location_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'text-body-small')]")
            return location_element.text.strip()
        except:
            return ""
    
    def _extract_education(self) -> List[Dict]:
        """Extract education information"""
        education_list = []
        
        try:
            # Click education section
            education_section = self.driver.find_element(By.XPATH, "//section[contains(@data-section, 'education')]")
            self.driver.execute_script("arguments[0].scrollIntoView();", education_section)
            
            # Find all education entries
            education_items = education_section.find_elements(By.XPATH, ".//li[contains(@class, 'profile-section-card')]")
            
            for item in education_items:
                try:
                    school = item.find_element(By.XPATH, ".//h3").text.strip()
                    
                    # Degree and field of study
                    degree_element = item.find_elements(By.XPATH, ".//h4")
                    degree = degree_element[0].text.strip() if degree_element else ""
                    
                    # Years
                    time_element = item.find_elements(By.XPATH, ".//time")
                    years = time_element[0].text.strip() if time_element else ""
                    
                    education_list.append({
                        'institution': school,
                        'degree': degree,
                        'years': years
                    })
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error extracting education: {e}")
        
        return education_list
    
    def _extract_experience(self) -> List[Dict]:
        """Extract work experience"""
        experience_list = []
        
        try:
            # Find experience section
            experience_section = self.driver.find_element(By.XPATH, "//section[contains(@data-section, 'experience')]")
            self.driver.execute_script("arguments[0].scrollIntoView();", experience_section)
            
            # Find all experience entries
            experience_items = experience_section.find_elements(By.XPATH, ".//li[contains(@class, 'profile-section-card')]")
            
            for item in experience_items:
                try:
                    title = item.find_element(By.XPATH, ".//h3").text.strip()
                    company = item.find_element(By.XPATH, ".//h4").text.strip()
                    
                    # Duration
                    duration_element = item.find_elements(By.XPATH, ".//time")
                    duration = duration_element[0].text.strip() if duration_element else ""
                    
                    experience_list.append({
                        'title': title,
                        'company': company,
                        'duration': duration
                    })
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error extracting experience: {e}")
        
        return experience_list
    
    def _extract_contact_info(self) -> Dict:
        """Extract contact information"""
        contact_info = {}
        
        try:
            # Click contact info button
            contact_button = self.driver.find_element(By.XPATH, "//a[contains(@href, 'detail/contact-info')]")
            contact_button.click()
            
            time.sleep(2)  # Wait for modal to load
            
            # Extract email
            try:
                email_element = self.driver.find_element(By.XPATH, "//a[contains(@href, 'mailto:')]")
                contact_info['email'] = email_element.get_attribute('href').replace('mailto:', '')
            except:
                pass
            
            # Extract phone
            try:
                phone_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'pv-contact-info__contact-type') and text()='Phone']/following-sibling::span")
                contact_info['phone'] = phone_element.text.strip()
            except:
                pass
            
            # Close modal
            close_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']")
            close_button.click()
            
        except Exception as e:
            print(f"Error extracting contact info: {e}")
        
        return contact_info
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
```

### 5. Anti-Detection Mixin

```python
# src/scrapers/anti_detection.py
import time
import random
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

class AntiDetectionMixin:
    """Mixin class for anti-detection techniques"""
    
    def random_delay(self, min_delay: float = None, max_delay: float = None):
        """Random delay between actions"""
        min_delay = min_delay or settings.REQUEST_DELAY_MIN
        max_delay = max_delay or settings.REQUEST_DELAY_MAX
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def simulate_typing(self, element, text: str):
        """Simulate human-like typing"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
    
    def simulate_scroll(self):
        """Simulate random scrolling"""
        actions = ActionChains(self.driver)
        
        # Random scroll down
        scroll_amount = random.randint(200, 800)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self.random_delay(0.5, 1.5)
        
        # Sometimes scroll back up a bit
        if random.random() < 0.3:
            scroll_back = random.randint(50, 200)
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
            self.random_delay(0.3, 1.0)
    
    def simulate_mouse_movement(self):
        """Simulate random mouse movements"""
        actions = ActionChains(self.driver)
        
        # Get window size
        window_size = self.driver.get_window_size()
        max_x = window_size['width']
        max_y = window_size['height']
        
        # Random movements
        for _ in range(random.randint(1, 3)):
            x = random.randint(0, max_x)
            y = random.randint(0, max_y)
            actions.move_by_offset(x, y)
            time.sleep(random.uniform(0.1, 0.5))
        
        actions.perform()
    
    def _scroll_to_load_sections(self):
        """Scroll through profile to load all sections"""
        # Scroll to different sections to trigger lazy loading
        sections = [
            "experience",
            "education", 
            "skills",
            "recommendations"
        ]
        
        for section in sections:
            try:
                element = self.driver.find_element(By.XPATH, f"//section[contains(@data-section, '{section}')]")
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
                self.random_delay(1, 2)
            except:
                continue
    
    def _go_to_next_page(self) -> bool:
        """Navigate to next page of search results"""
        try:
            next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Next']")
            if next_button.is_enabled():
                next_button.click()
                self.random_delay(2, 4)
                return True
            return False
        except:
            return False
```

### 6. GitHub Monitor Implementation

```python
# src/scrapers/github_monitor.py
import requests
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from github import Github

from ..models.profile import JobPosting
from ..utils.config import settings

class GitHubMonitor:
    def __init__(self):
        self.github = Github(settings.GITHUB_TOKEN) if settings.GITHUB_TOKEN else None
        self.internship_keywords = [
            'intern', 'internship', 'summer intern', 'co-op', 'coop',
            'student', 'graduate program', 'entry level', 'new grad'
        ]
    
    def monitor_repositories(self, repo_urls: List[str]) -> List[JobPosting]:
        """Monitor GitHub repositories for new job postings"""
        job_postings = []
        
        for repo_url in repo_urls:
            try:
                company_name = self._extract_company_from_repo(repo_url)
                print(f"Monitoring {company_name} repository...")
                
                repo_jobs = self._scan_repository(repo_url, company_name)
                job_postings.extend(repo_jobs)
                
            except Exception as e:
                print(f"Error monitoring repository {repo_url}: {e}")
        
        return job_postings
    
    def _scan_repository(self, repo_url: str, company_name: str) -> List[JobPosting]:
        """Scan a repository for job postings"""
        job_postings = []
        
        try:
            # Extract repo info from URL
            repo_path = repo_url.replace('https://github.com/', '')
            repo = self.github.get_repo(repo_path)
            
            # Check recent commits (last 30 days)
            since = datetime.now() - timedelta(days=30)
            commits = repo.get_commits(since=since)
            
            for commit in commits:
                # Check commit message and files for job-related content
                if self._contains_job_keywords(commit.commit.message):
                    job_data = self._extract_job_from_commit(commit, company_name, repo_url)
                    if job_data:
                        job_postings.append(job_data)
                
                # Check modified files
                for file in commit.files:
                    if self._is_job_related_file(file.filename):
                        job_data = self._extract_job_from_file(file, commit, company_name, repo_url)
                        if job_data:
                            job_postings.append(job_data)
            
            # Also check README and other job-related files
            job_postings.extend(self._scan_job_files(repo, company_name, repo_url))
            
        except Exception as e:
            print(f"Error scanning repository: {e}")
        
        return job_postings
    
    def _contains_job_keywords(self, text: str) -> bool:
        """Check if text contains job/internship keywords"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.internship_keywords)
    
    def _is_job_related_file(self, filename: str) -> bool:
        """Check if filename suggests job-related content"""
        job_file_patterns = [
            r'.*job.*\.md',
            r'.*career.*\.md', 
            r'.*intern.*\.md',
            r'README\.md',
            r'JOBS\.md',
            r'HIRING\.md'
        ]
        
        filename_lower = filename.lower()
        return any(re.match(pattern, filename_lower) for pattern in job_file_patterns)
    
    def _extract_job_from_commit(self, commit, company_name: str, repo_url: str) -> Optional[JobPosting]:
        """Extract job posting information from commit"""
        try:
            # Basic job posting structure
            job_data = JobPosting()
            job_data.id = f"{company_name}_{commit.sha[:8]}"
            job_data.company = company_name
            job_data.title = self._extract_job_title(commit.commit.message)
            job_data.description = commit.commit.message
            job_data.posted_date = commit.commit.author.date
            job_data.github_repo = repo_url
            job_data.commit_hash = commit.sha
            job_data.raw_content = commit.commit.message
            
            # Extract keywords
            job_data.keywords = self._extract_keywords(commit.commit.message)
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting job from commit: {e}")
            return None
    
    def _extract_job_from_file(self, file, commit, company_name: str, repo_url: str) -> Optional[JobPosting]:
        """Extract job posting from modified file"""
        try:
            # Get file content
            if file.patch and self._contains_job_keywords(file.patch):
                job_data = JobPosting()
                job_data.id = f"{company_name}_{file.filename}_{commit.sha[:8]}"
                job_data.company = company_name
                job_data.title = self._extract_job_title_from_file(file.filename, file.patch)
                job_data.description = file.patch
                job_data.posted_date = commit.commit.author.date
                job_data.github_repo = repo_url
                job_data.commit_hash = commit.sha
                job_data.raw_content = file.patch
                job_data.keywords = self._extract_keywords(file.patch)
                
                return job_data
                
        except Exception as e:
            print(f"Error extracting job from file: {e}")
            
        return None
    
    def _scan_job_files(self, repo, company_name: str, repo_url: str) -> List[JobPosting]:
        """Scan repository for existing job-related files"""
        job_postings = []
        
        try:
            # Check common job file locations
            job_file_paths = [
                'README.md',
                'JOBS.md',
                'CAREERS.md',
                'HIRING.md',
                'jobs/README.md',
                'careers/README.md'
            ]
            
            for file_path in job_file_paths:
                try:
                    file_content = repo.get_contents(file_path)
                    content = file_content.decoded_content.decode('utf-8')
                    
                    if self._contains_job_keywords(content):
                        job_postings.extend(self._parse_job_file_content(content, company_name, repo_url))
                        
                except:
                    continue  # File doesn't exist
                    
        except Exception as e:
            print(f"Error scanning job files: {e}")
        
        return job_postings
    
    def _parse_job_file_content(self, content: str, company_name: str, repo_url: str) -> List[JobPosting]:
        """Parse job file content for multiple job postings"""
        job_postings = []
        
        # Split content into sections (could be multiple jobs)
        sections = re.split(r'\n#{1,3}\s+', content)
        
        for i, section in enumerate(sections):
            if self._contains_job_keywords(section):
                job_data = JobPosting()
                job_data.id = f"{company_name}_file_{i}"
                job_data.company = company_name
                job_data.title = self._extract_job_title(section)
                job_data.description = section
                job_data.posted_date = datetime.now()
                job_data.github_repo = repo_url
                job_data.raw_content = section
                job_data.keywords = self._extract_keywords(section)
                
                job_postings.append(job_data)
        
        return job_postings
    
    def _extract_job_title(self, text: str) -> str:
        """Extract job title from text"""
        # Look for common patterns
        patterns = [
            r'(software engineer intern)',
            r'(data scientist intern)',
            r'(product manager intern)',
            r'(.*intern.*)',
            r'(new grad.*)',
            r'(entry level.*)',
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).title()
        
        # Fallback: use first line or first few words
        first_line = text.split('\n')[0].strip()
        return first_line[:100] if first_line else "Job Posting"
    
    def _extract_job_title_from_file(self, filename: str, content: str) -> str:
        """Extract job title from filename and content"""
        # First try to extract from content
        title = self._extract_job_title(content)
        
        if title == "Job Posting":
            # Try to get from filename
            if 'intern' in filename.lower():
                return "Internship Position"
            elif 'job' in filename.lower():
                return "Job Opening"
        
        return title
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from job posting text"""
        keywords = []
        
        # Technology keywords
        tech_keywords = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql',
            'aws', 'docker', 'kubernetes', 'machine learning', 'ai',
            'data science', 'backend', 'frontend', 'full stack'
        ]
        
        text_lower = text.lower()
        for keyword in tech_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # Add internship keywords that are present
        for keyword in self.internship_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return list(set(keywords))  # Remove duplicates
    
    def _extract_company_from_repo(self, repo_url: str) -> str:
        """Extract company name from repository URL"""
        # Extract from GitHub URL pattern
        match = re.search(r'github\.com/([^/]+)', repo_url)
        if match:
            return match.group(1).replace('-', ' ').title()
        
        return "Unknown Company"
    
    def find_company_employees(self, company_name: str) -> List[str]:
        """Find LinkedIn profiles of company employees"""
        # This would integrate with the LinkedIn scraper
        # to find employees at the company
        
        search_criteria = {
            'current_company': company_name,
            'keywords': 'software engineer developer',
            'max_pages': 3
        }
        
        # Return list of profile URLs (to be scraped later)
        return []  # Placeholder
```

### 7. Filter System Implementation

```python
# src/filters/education_filter.py
from typing import List, Dict
from fuzzywuzzy import fuzz
from ..models.profile import Profile, Education

class EducationFilter:
    def __init__(self, target_schools: List[str]):
        self.target_schools = [school.lower() for school in target_schools]
        
        # Common abbreviations and variations
        self.school_mappings = {
            'mit': 'massachusetts institute of technology',
            'stanford': 'stanford university',
            'uc berkeley': 'university of california berkeley',
            'caltech': 'california institute of technology',
            'cmu': 'carnegie mellon university',
            'georgia tech': 'georgia institute of technology'
        }
    
    def matches_education(self, profile: Profile) -> bool:
        """Check if profile's education matches target schools"""
        if not self.target_schools:
            return True  # No filter applied
        
        for education in profile.education:
            if self._school_matches(education.institution):
                return True
        
        return False
    
    def _school_matches(self, school: str) -> bool:
        """Check if a school matches any target school"""
        school_lower = school.lower()
        
        # Direct match
        if school_lower in self.target_schools:
            return True
        
        # Check abbreviations
        normalized_school = self.school_mappings.get(school_lower, school_lower)
        if normalized_school in self.target_schools:
            return True
        
        # Fuzzy matching for typos and variations
        for target_school in self.target_schools:
            similarity = fuzz.partial_ratio(school_lower, target_school)
            if similarity > 85:  # 85% similarity threshold
                return True
        
        return False
    
    def get_education_match_score(self, profile: Profile) -> float:
        """Get a score (0-1) for how well education matches"""
        if not self.target_schools:
            return 1.0
        
        max_score = 0.0
        
        for education in profile.education:
            school_lower = education.institution.lower()
            
            for target_school in self.target_schools:
                # Exact match
                if school_lower == target_school:
                    return 1.0
                
                # Fuzzy match score
                similarity = fuzz.ratio(school_lower, target_school) / 100.0
                max_score = max(max_score, similarity)
        
        return max_score

# src/filters/role_matcher.py
class RoleMatcher:
    def __init__(self):
        self.role_keywords = {
            'software_engineer': [
                'software engineer', 'software developer', 'backend engineer',
                'frontend engineer', 'full stack engineer', 'web developer'
            ],
            'data_scientist': [
                'data scientist', 'data analyst', 'machine learning engineer',
                'ai engineer', 'research scientist'
            ],
            'product_manager': [
                'product manager', 'product owner', 'program manager'
            ],
            'designer': [
                'ux designer', 'ui designer', 'product designer', 'graphic designer'
            ]
        }
    
    def match_role_similarity(self, internship_description: str, profile_role: str) -> float:
        """Calculate similarity between internship and profile role"""
        internship_lower = internship_description.lower()
        profile_lower = profile_role.lower()
        
        # Direct keyword matching
        for role_category, keywords in self.role_keywords.items():
            internship_matches = any(keyword in internship_lower for keyword in keywords)
            profile_matches = any(keyword in profile_lower for keyword in keywords)
            
            if internship_matches and profile_matches:
                return 1.0
        
        # Fuzzy string matching
        similarity = fuzz.ratio(internship_lower, profile_lower) / 100.0
        
        # Boost score if both contain "engineer", "manager", etc.
        common_terms = ['engineer', 'manager', 'developer', 'analyst', 'scientist']
        for term in common_terms:
            if term in internship_lower and term in profile_lower:
                similarity += 0.2
        
        return min(similarity, 1.0)
```

### 8. API Implementation

```python
# src/api/routes.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel

from ..scrapers.linkedin_scraper import LinkedInScraper
from ..scrapers.github_monitor import GitHubMonitor
from ..filters.education_filter import EducationFilter
from ..database.connection import get_db_session
from ..models.profile import Profile, JobPosting

app = FastAPI(title="LinkedIn Scraper API")

class SearchRequest(BaseModel):
    keywords: Optional[str] = None
    current_company: Optional[str] = None
    school: Optional[str] = None
    location: Optional[str] = None
    max_pages: int = 5

class ProfileResponse(BaseModel):
    id: str
    name: str
    headline: str
    current_company: str
    linkedin_url: str

@app.post("/search/profiles", response_model=List[ProfileResponse])
async def search_profiles(request: SearchRequest, background_tasks: BackgroundTasks):
    """Search for LinkedIn profiles"""
    try:
        scraper = LinkedInScraper()
        
        # Add background task for scraping
        background_tasks.add_task(
            scrape_profiles_background,
            request.dict()
        )
        
        return {"message": "Search started. Check /profiles endpoint for results."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles", response_model=List[ProfileResponse])
async def get_profiles(skip: int = 0, limit: int = 100):
    """Get scraped profiles from database"""
    try:
        with get_db_session() as session:
            profiles = session.query(Profile).offset(skip).limit(limit).all()
            return profiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitor/github")
async def monitor_github_repos(repo_urls: List[str], background_tasks: BackgroundTasks):
    """Start monitoring GitHub repositories"""
    try:
        background_tasks.add_task(
            monitor_github_background,
            repo_urls
        )
        
        return {"message": f"Started monitoring {len(repo_urls)} repositories"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
async def get_job_postings(skip: int = 0, limit: int = 50):
    """Get detected job postings"""
    try:
        with get_db_session() as session:
            jobs = session.query(JobPosting).offset(skip).limit(limit).all()
            return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def scrape_profiles_background(search_criteria: dict):
    """Background task for profile scraping"""
    scraper = LinkedInScraper()
    
    try:
        scraper.setup_driver()
        
        if settings.LINKEDIN_EMAIL and settings.LINKEDIN_PASSWORD:
            scraper.login(settings.LINKEDIN_EMAIL, settings.LINKEDIN_PASSWORD)
        
        # Search for profiles
        profile_urls = scraper.search_profiles(search_criteria)
        
        # Scrape each profile
        with get_db_session() as session:
            for url in profile_urls:
                profile_data = scraper.scrape_profile(url)
                if profile_data:
                    # Save to database
                    profile = Profile(**profile_data)
                    session.add(profile)
                    session.commit()
        
    finally:
        scraper.cleanup()

async def monitor_github_background(repo_urls: List[str]):
    """Background task for GitHub monitoring"""
    monitor = GitHubMonitor()
    
    job_postings = monitor.monitor_repositories(repo_urls)
    
    # Save job postings to database
    with get_db_session() as session:
        for job in job_postings:
            session.add(job)
        session.commit()
```

### 9. Database Connection

```python
# src/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from ..utils.config import settings
from ..models.profile import Base

# Create database engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session():
    """Get database session with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

### 10. Main Application Entry Point

```python
# main.py
import uvicorn
from src.api.routes import app
from src.database.connection import create_tables
from src.utils.config import settings

def main():
    """Main application entry point"""
    # Create database tables
    create_tables()
    
    # Start the API server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
```

### 11. Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/linkedin_scraper
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: linkedin_scraper
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: celery -A src.tasks worker --loglevel=info
    depends_on:
      - redis
      - db
    volumes:
      - .:/app

volumes:
  postgres_data:
```

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1) \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION})/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
```

## Usage Instructions

### 1. Basic Setup
```bash
# Clone and setup
git clone <repository>
cd linkedin-scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Run with Docker
```bash
docker-compose up -d
```

### 3. API Usage Examples

```bash
# Search for profiles
curl -X POST "http://localhost:8000/search/profiles" \
     -H "Content-Type: application/json" \
     -d '{
       "keywords": "software engineer",
       "school": "Stanford University",
       "max_pages": 3
     }'

# Get scraped profiles
curl "http://localhost:8000/profiles?limit=50"

# Monitor GitHub repositories
curl -X POST "http://localhost:8000/monitor/github" \
     -H "Content-Type: application/json" \
     -d '["https://github.com/company/repo"]'

# Get job postings
curl "http://localhost:8000/jobs"
```

### 4. Manual Script Usage

```python
# example_usage.py
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.filters.education_filter import EducationFilter

# Initialize scraper
scraper = LinkedInScraper()
scraper.setup_driver()

# Login (optional)
scraper.login("your-email@example.com", "your-password")

# Search criteria
search_criteria = {
    'keywords': 'software engineer',
    'school': 'Stanford University',
    'current_company': 'Google',
    'max_pages': 2
}

# Search and scrape
profile_urls = scraper.search_profiles(search_criteria)
for url in profile_urls[:5]:  # Limit to first 5
    profile_data = scraper.scrape_profile(url)
    print(f"Scraped: {profile_data['name']}")

scraper.cleanup()
```

## Next Steps

1. **Configure your settings** in `.env`
2. **Test the basic scraping** with a small dataset
3. **Set up monitoring** for target GitHub repositories
4. **Implement additional filters** as needed
5. **Add error handling and logging**
6. **Scale with proxy services** if needed

## Important Notes

⚠️ **Legal Compliance**: Always review LinkedIn's Terms of Service and applicable laws before scraping. Consider using LinkedIn's official APIs where possible.

⚠️ **Rate Limiting**: Implement conservative rate limiting to avoid being blocked.

⚠️ **Data Privacy**: Ensure proper handling of personal data and compliance with privacy regulations.

⚠️ **Monitoring**: Set up proper monitoring and alerting for production use. 