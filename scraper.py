import sys
import site
import logging
import os
import json
import time
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from itertools import product

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    config_path = 'config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.70 Safari/537.36")
    
    service = ChromeService(executable_path="/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_emails(text):
    email_pattern = r'[a-zA-Z0-9_.+-]+@gmail\.com'
    return re.findall(email_pattern, text)

def save_emails(emails, output_file='emails.txt'):
    try:
        unique_emails = sorted(set(emails))
        with open(output_file, 'a') as f:
            for email in unique_emails:
                f.write(email + '\n')
        logger.info(f"Saved {len(unique_emails)} unique emails to {output_file}")
    except Exception as e:
        logger.error(f"Error saving emails: {e}")

def perform_search(driver, query, start):
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.google.com/search?q={encoded_query}&start={start}"
    driver.get(search_url)
    
    try:
        consent_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all')]"))
        )
        consent_button.click()
    except TimeoutException:
        pass
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
    except TimeoutException:
        logger.error("Timed out waiting for search results")
        raise

def scrape_emails(driver, name, domain, niche, num_pages=5):
    logger.info(f"Scraping emails for {name} - {niche}")
    collected_emails = set()
    for page in range(num_pages):
        start = page * 10 + 1
        query = f'"{name}" "{domain}" "{niche}"'
        perform_search(driver, query, start)
        time.sleep(2)  # Wait for the page to load
        page_source = driver.page_source
        emails = get_emails(page_source)
        logger.info(f"Found {len(emails)} emails on page {page + 1} for {name} - {niche}")
        collected_emails.update(emails)
        
        # Save emails after each page to avoid data loss
        save_emails(collected_emails, f"emails_{name.replace(' ', '_')}_{domain}_{niche.replace(' ', '_')}.txt")
    
    logger.info(f"Finished scraping for {name} - {niche}. Total emails collected: {len(collected_emails)}")
    return collected_emails

def main():
    config = load_config()
    names = [name.strip() for name in config['names'].split(',')]
    niches = [niche.strip() for niche in config['niche'].split(',')]
    domain = config['domain']
    
    driver = initialize_driver()
    
    all_emails = set()
    for name, niche in product(names, niches):
        try:
            emails = scrape_emails(driver, name, domain, niche)
            all_emails.update(emails)
        except Exception as e:
            logger.error(f"Error processing query for name '{name}' and niche '{niche}': {str(e)}")
            continue  # Move to the next combination
    
    driver.quit()
    
    # Save the final combined result
    save_emails(all_emails, 'final_combined_emails.txt')
    logger.info("Scraping process completed")

if __name__ == "__main__":
    main()