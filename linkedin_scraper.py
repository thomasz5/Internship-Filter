#!/usr/bin/env python3
"""
Simple LinkedIn Scraper for University of Washington Alumni
Focus: Find UW Seattle alumni at companies with internship openings
Data: Name, Title, Company only
"""

import time
import random
import sqlite3
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from config import Config

class UWLinkedInScraper:
    def __init__(self):
        self.config = Config()
        self.driver = None
        self.wait = None
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Setup Chrome driver with anti-detection"""
        options = Options()
        
        # Basic stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use a realistic user agent
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
        self.logger.info("Chrome driver initialized")
    
    def login(self) -> bool:
        """Login to LinkedIn"""
        if not self.config.LINKEDIN_EMAIL or not self.config.LINKEDIN_PASSWORD:
            self.logger.warning("LinkedIn credentials not provided")
            return False
        
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Enter email
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            self._type_slowly(email_field, self.config.LINKEDIN_EMAIL)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            self._type_slowly(password_field, self.config.LINKEDIN_PASSWORD)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if we're logged in (look for feed or home)
            if "feed" in self.driver.current_url or "linkedin.com/in" in self.driver.current_url:
                self.logger.info("Successfully logged into LinkedIn")
                return True
            else:
                self.logger.warning("Login may have failed - unexpected URL")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    def search_uw_alumni_at_company(self, company_name: str) -> List[Dict]:
        """Search for UW alumni at a specific company"""
        try:
            # Build search URL for UW alumni at the company
            search_query = f'school:"University of Washington" AND company:"{company_name}"'
            encoded_query = search_query.replace(' ', '%20').replace('"', '%22')
            
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_query}"
            
            self.logger.info(f"Searching for UW alumni at {company_name}")
            self.driver.get(search_url)
            
            # Wait for search results
            time.sleep(3)
            
            profiles = []
            max_pages = min(self.config.MAX_PAGES_PER_SEARCH, 3)  # Limit to 3 pages max
            
            for page in range(max_pages):
                self.logger.info(f"Scraping page {page + 1} for {company_name}")
                
                # Get profiles from current page
                page_profiles = self._extract_profiles_from_page(company_name)
                profiles.extend(page_profiles)
                
                # Stop if we have enough or this is the last page
                if len(profiles) >= self.config.MAX_PROFILES_PER_COMPANY:
                    break
                
                # Try to go to next page
                if not self._go_to_next_page():
                    break
                
                # Random delay between pages
                time.sleep(random.uniform(3, 6))
            
            self.logger.info(f"Found {len(profiles)} UW alumni at {company_name}")
            return profiles[:self.config.MAX_PROFILES_PER_COMPANY]
            
        except Exception as e:
            self.logger.error(f"Error searching for {company_name}: {e}")
            return []
    
    def _extract_profiles_from_page(self, company_name: str) -> List[Dict]:
        """Extract profile data from current search results page"""
        profiles = []
        
        try:
            # Wait for search results to load
            search_results = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".search-result__wrapper"))
            )
            
            for result in search_results:
                try:
                    profile = self._extract_single_profile(result, company_name)
                    if profile:
                        profiles.append(profile)
                except Exception as e:
                    self.logger.debug(f"Error extracting profile: {e}")
                    continue
                    
        except TimeoutException:
            self.logger.warning("No search results found or page load timeout")
        except Exception as e:
            self.logger.error(f"Error extracting profiles from page: {e}")
        
        return profiles
    
    def _extract_single_profile(self, result_element, company_name: str) -> Optional[Dict]:
        """Extract data from a single profile search result"""
        try:
            # Get name
            name_element = result_element.find_element(By.CSS_SELECTOR, ".actor-name")
            name = name_element.text.strip()
            
            # Get LinkedIn URL
            profile_link = result_element.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
            linkedin_url = profile_link.get_attribute("href")
            
            # Get title/headline
            try:
                title_element = result_element.find_element(By.CSS_SELECTOR, ".subline-level-1")
                title = title_element.text.strip()
            except NoSuchElementException:
                title = "Not specified"
            
            # Basic validation
            if not name or not linkedin_url:
                return None
            
            # Check if this person actually attended UW (sometimes search results are fuzzy)
            if not self._verify_uw_connection(result_element):
                return None
            
            return {
                'name': name,
                'title': title,
                'company': company_name,
                'linkedin_url': linkedin_url,
                'college_match': 1,  # Confirmed UW
                'discovered_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.debug(f"Error extracting single profile: {e}")
            return None
    
    def _verify_uw_connection(self, result_element) -> bool:
        """Verify that this person actually has University of Washington connection"""
        try:
            # Look for UW mention in the profile snippet
            text_content = result_element.text.lower()
            uw_indicators = [
                'university of washington',
                'uw seattle',
                'university of washington seattle',
                'washington university'  # Sometimes abbreviated
            ]
            
            return any(indicator in text_content for indicator in uw_indicators)
            
        except Exception:
            return True  # If we can't verify, assume it's valid since it came from our search
    
    def _go_to_next_page(self) -> bool:
        """Navigate to next page of search results"""
        try:
            # Look for next button
            next_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Next']")
            
            if next_button.is_enabled():
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
                return True
            else:
                return False
                
        except NoSuchElementException:
            self.logger.debug("No next button found")
            return False
        except Exception as e:
            self.logger.debug(f"Error navigating to next page: {e}")
            return False
    
    def _type_slowly(self, element, text: str):
        """Type text slowly to mimic human behavior"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def save_profiles(self, profiles: List[Dict]):
        """Save profiles to database"""
        if not profiles:
            return
        
        conn = sqlite3.connect(self.config.DATABASE_PATH)
        
        for profile in profiles:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO profiles 
                    (name, title, company, linkedin_url, college_match, discovered_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    profile['name'],
                    profile['title'],
                    profile['company'],
                    profile['linkedin_url'],
                    profile['college_match'],
                    profile['discovered_date']
                ))
                
            except sqlite3.IntegrityError:
                # Profile already exists
                pass
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Saved {len(profiles)} profiles to database")
    
    def scrape_companies(self, company_names: List[str]):
        """Scrape UW alumni from multiple companies"""
        if not company_names:
            self.logger.info("No companies to scrape")
            return
        
        self.setup_driver()
        
        if not self.login():
            self.logger.error("Failed to login - skipping LinkedIn scraping")
            self.cleanup()
            return
        
        all_profiles = []
        
        for company in company_names:
            try:
                self.logger.info(f"Searching UW alumni at {company}")
                
                profiles = self.search_uw_alumni_at_company(company)
                
                if profiles:
                    all_profiles.extend(profiles)
                    self.save_profiles(profiles)
                    
                    print(f"✅ Found {len(profiles)} UW alumni at {company}")
                    for profile in profiles[:3]:  # Show first 3
                        print(f"   • {profile['name']} - {profile['title']}")
                    if len(profiles) > 3:
                        print(f"   • ... and {len(profiles) - 3} more")
                else:
                    print(f"❌ No UW alumni found at {company}")
                
                # Longer delay between companies to be respectful
                time.sleep(random.uniform(self.config.REQUEST_DELAY_MIN, self.config.REQUEST_DELAY_MAX))
                
            except Exception as e:
                self.logger.error(f"Error scraping {company}: {e}")
                continue
        
        self.cleanup()
        
        if all_profiles:
            print(f"\n🎓 Total: Found {len(all_profiles)} UW alumni across all companies!")
        else:
            print("No UW alumni found at any of the target companies.")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser closed")

if __name__ == "__main__":
    scraper = UWLinkedInScraper()
    
    # Test with a few companies
    test_companies = ["Microsoft", "Amazon", "Boeing"]
    scraper.scrape_companies(test_companies) 