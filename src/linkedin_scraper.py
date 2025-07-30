#!/usr/bin/env python3
"""
Simple LinkedIn Scraper for University of Washington Alumni
Focus: Find UW Seattle alumni at companies with internship openings
Data: Name, Title, Company only
"""

import time
import random
import sqlite3
import os
import tempfile
import shutil
import pickle
import json
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
        self.temp_user_data_dir = None
        self.session_file = "linkedin_session.pkl"
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
    
    def setup_driver(self, headless=None):
        """Setup Chrome driver with anti-detection"""
        options = Options()
        
        # Create unique temporary directory for this session
        self.temp_user_data_dir = tempfile.mkdtemp(prefix='chrome_user_data_')
        
        # Find available port for remote debugging
        import socket
        sock = socket.socket()
        sock.bind(('', 0))
        debug_port = sock.getsockname()[1]
        sock.close()
        
        # Basic stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Headless mode decision
        # If headless is not specified, check if we have a saved session
        if headless is None:
            headless = os.path.exists(self.session_file)
        
        if headless:
            options.add_argument('--headless')  # Run without GUI
            self.logger.info("Running in headless mode")
        else:
            self.logger.info("Running with GUI for manual verification")
        
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-data-dir={self.temp_user_data_dir}')  # Unique user data directory
        options.add_argument(f'--remote-debugging-port={debug_port}')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Use a realistic user agent
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            self.logger.info(f"Chrome driver initialized with user data dir: {self.temp_user_data_dir}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            self.cleanup_temp_dir()
            raise
    
    def save_session(self):
        """Save LinkedIn session cookies to file"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.session_file, 'wb') as f:
                pickle.dump(cookies, f)
            self.logger.info(f"Session saved to {self.session_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save session: {e}")
    
    def load_session(self) -> bool:
        """Load LinkedIn session cookies from file"""
        try:
            if not os.path.exists(self.session_file):
                self.logger.info("No session file found")
                return False
            
            # Go to LinkedIn first to set domain
            self.driver.get("https://www.linkedin.com")
            time.sleep(2)
            
            with open(self.session_file, 'rb') as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    self.logger.debug(f"Could not add cookie {cookie.get('name', 'unknown')}: {e}")
            
            # Refresh page to use cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Check if we're logged in
            current_url = self.driver.current_url
            if "feed" in current_url or "/in/" in current_url or "linkedin.com/in" in self.driver.page_source:
                self.logger.info("Session restored successfully!")
                return True
            else:
                self.logger.info("Session expired or invalid")
                return False
                
        except Exception as e:
            self.logger.warning(f"Failed to load session: {e}")
            return False
    
    def login(self) -> bool:
        """Login to LinkedIn with session persistence"""
        if not self.config.LINKEDIN_EMAIL or not self.config.LINKEDIN_PASSWORD:
            self.logger.warning("LinkedIn credentials not provided")
            return False
        
        # First try to load existing session
        self.logger.info("Attempting to load existing LinkedIn session...")
        if self.load_session():
            return True
        
        # If no session or session expired, do fresh login
        self.logger.info("No valid session found, performing fresh login...")
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
            
            current_url = self.driver.current_url
            
            # Check for security challenge
            if "challenge" in current_url or "checkpoint" in current_url:
                self.logger.warning("LinkedIn security challenge detected!")
                self.logger.warning("Please complete the challenge in the browser window, then press Enter...")
                
                # Wait for user to complete challenge
                input("Press Enter after completing the LinkedIn security challenge...")
                
                # Check again
                time.sleep(3)
                current_url = self.driver.current_url
            
            # Check if we're logged in (look for feed or home)
            if "feed" in current_url or "linkedin.com/in" in current_url or "/in/" in current_url:
                self.logger.info("Successfully logged into LinkedIn")
                # Save session for future use
                self.save_session()
                return True
            else:
                self.logger.warning(f"Login may have failed - current URL: {current_url}")
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
            self.logger.debug(f"Search URL: {search_url}")
            self.driver.get(search_url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Debug: Log page title and URL
            self.logger.debug(f"Page title: {self.driver.title}")
            self.logger.debug(f"Current URL: {self.driver.current_url}")
            
            # Check if we're on the right page
            if "search" not in self.driver.current_url:
                self.logger.warning("Redirected away from search page - possibly need to re-login")
                return []
            
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
            # Debug: Take screenshot and log page source snippet
            self.logger.debug("Looking for search results...")
            
            # Log a snippet of page source to understand structure
            page_source_snippet = self.driver.page_source[:1000]
            self.logger.debug(f"Page source snippet: {page_source_snippet}")
            
            # Try multiple approaches to find search results
            search_result_selectors = [
                ".entity-result__item",
                ".reusable-search__result-container",
                "[data-chameleon-result-urn]",
                ".search-result__wrapper",
                ".search-results-container .search-result",
                ".search-result",
                ".entity-result"
            ]
            
            search_results = []
            for selector in search_result_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.logger.debug(f"Found {len(elements)} results with selector: {selector}")
                        search_results = elements
                        break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not search_results:
                # Last resort - try to find any clickable profile links
                try:
                    profile_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
                    self.logger.debug(f"Found {len(profile_links)} profile links as fallback")
                    if profile_links:
                        # Create mock elements for each profile link
                        for link in profile_links[:10]:  # Limit to first 10
                            try:
                                parent = link.find_element(By.XPATH, "..")
                                search_results.append(parent)
                            except:
                                search_results.append(link)
                except Exception as e:
                    self.logger.debug(f"Fallback approach failed: {e}")
            
            if search_results:
                self.logger.info(f"Processing {len(search_results)} search results")
                for i, result in enumerate(search_results):
                    try:
                        self.logger.debug(f"Processing result {i+1}")
                        profile = self._extract_single_profile(result, company_name)
                        if profile:
                            profiles.append(profile)
                            self.logger.debug(f"Successfully extracted profile: {profile['name']}")
                    except Exception as e:
                        self.logger.debug(f"Error extracting profile {i+1}: {e}")
                        continue
            else:
                self.logger.warning("No search results found with any selector")
                
        except Exception as e:
            self.logger.error(f"Error extracting profiles from page: {e}")
        
        return profiles
    
    def _extract_single_profile(self, result_element, company_name: str) -> Optional[Dict]:
        """Extract data from a single profile search result"""
        try:
            # Debug: Log element structure
            element_text = result_element.text[:200] if result_element.text else "No text"
            self.logger.debug(f"Processing element with text: {element_text}")
            
            # Get name - Updated selectors with more fallbacks
            name_element = None
            name = ""
            
            # Try multiple selectors for name - ordered by likelihood
            name_selectors = [
                ".entity-result__title-text a span[aria-hidden='true']",
                ".entity-result__title-text a",
                ".app-aware-link .visually-hidden",
                ".actor-name-with-distance span[aria-hidden='true']",
                ".actor-name",
                "[data-chameleon-result-urn] a span",
                "a[href*='/in/'] span[aria-hidden='true']",
                "a[href*='/in/']",
                ".search-result__info .actor-name",
                ".search-result__info a",
                ".name a",
                "h3 a",
                "h3",
                ".result-lockup__name a"
            ]
            
            for selector in name_selectors:
                try:
                    name_element = result_element.find_element(By.CSS_SELECTOR, selector)
                    name = name_element.text.strip()
                    if name and len(name) > 1:
                        self.logger.debug(f"Found name '{name}' with selector: {selector}")
                        break
                except:
                    continue
            
            # If still no name, try to extract from any text content
            if not name:
                try:
                    # Look for profile links and extract name from link text or nearby elements
                    profile_links = result_element.find_elements(By.CSS_SELECTOR, "a[href*='/in/']")
                    for link in profile_links:
                        link_text = link.text.strip()
                        if link_text and len(link_text) > 1 and not link_text.lower().startswith('view'):
                            name = link_text
                            self.logger.debug(f"Extracted name from link text: {name}")
                            break
                except:
                    pass
            
            if not name:
                self.logger.debug("Could not extract name from this element")
                return None
            
            # Get LinkedIn URL - Updated selectors with more fallbacks
            profile_link = None
            linkedin_url = ""
            
            link_selectors = [
                ".entity-result__title-text a",
                "a[href*='/in/']",
                ".app-aware-link",
                ".actor-name a",
                ".search-result__info a[href*='/in/']",
                ".result-lockup__name a"
            ]
            
            for selector in link_selectors:
                try:
                    profile_link = result_element.find_element(By.CSS_SELECTOR, selector)
                    linkedin_url = profile_link.get_attribute('href')
                    if linkedin_url and '/in/' in linkedin_url:
                        self.logger.debug(f"Found LinkedIn URL with selector: {selector}")
                        break
                except:
                    continue
            
            # Clean up LinkedIn URL
            if linkedin_url:
                # Remove tracking parameters
                if '?' in linkedin_url:
                    linkedin_url = linkedin_url.split('?')[0]
            
            # Get title/position - Updated selectors with more fallbacks
            title = ""
            title_selectors = [
                ".entity-result__primary-subtitle",
                ".entity-result__summary",
                ".subline-level-1",
                ".actor-mini-profile .actor-title",
                ".search-result__snippets",
                ".result-lockup__highlight",
                "[data-entity-urn] .t-14",
                ".t-14.t-black--light"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = result_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        self.logger.debug(f"Found title '{title}' with selector: {selector}")
                        break
                except:
                    continue
            
            # Get location if available
            location = ""
            location_selectors = [
                ".entity-result__secondary-subtitle",
                ".search-result__snippets .t-12",
                ".result-lockup__misc"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = result_element.find_element(By.CSS_SELECTOR, selector)
                    location = location_element.text.strip()
                    if location:
                        break
                except:
                    continue
            
            # Basic validation
            if not name:
                self.logger.debug("No name found, skipping profile")
                return None
            
            # Verify this person has UW connection
            if not self._verify_uw_connection(result_element):
                self.logger.debug(f"No UW connection verified for {name}")
                return None
            
            self.logger.debug(f"Successfully extracted profile: {name} - {title} at {company_name}")
            
            return {
                'name': name,
                'title': title or "Not specified",
                'company': company_name,
                'linkedin_url': linkedin_url,
                'location': location,
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
                    
                    print(f"Found {len(profiles)} UW alumni at {company}")
                    for profile in profiles[:3]:  # Show first 3
                        print(f"   • {profile['name']} - {profile['title']}")
                    if len(profiles) > 3:
                        print(f"   • ... and {len(profiles) - 3} more")
                else:
                    print(f"No UW alumni found at {company}")
                
                # Longer delay between companies to be respectful
                time.sleep(random.uniform(self.config.REQUEST_DELAY_MIN, self.config.REQUEST_DELAY_MAX))
                
            except Exception as e:
                self.logger.error(f"Error scraping {company}: {e}")
                continue
        
        self.cleanup()
        
        if all_profiles:
            print(f"\nTotal: Found {len(all_profiles)} UW alumni across all companies!")
        else:
            print("No UW alumni found at any of the target companies.")
    
    def cleanup_temp_dir(self):
        """Clean up temporary user data directory"""
        if self.temp_user_data_dir and os.path.exists(self.temp_user_data_dir):
            try:
                shutil.rmtree(self.temp_user_data_dir)
                self.logger.info(f"Cleaned up temp directory: {self.temp_user_data_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp directory: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Browser closed")
        self.cleanup_temp_dir()

if __name__ == "__main__":
    scraper = UWLinkedInScraper()
    
    # Test with a few companies
    test_companies = ["Microsoft", "Amazon", "Boeing"]
    scraper.scrape_companies(test_companies) 