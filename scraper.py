import sys
import logging
import os
import json
import time
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def load_config():
    config_path = 'config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
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
    return webdriver.Chrome(service=service, options=chrome_options)

def get_emails(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@gmail\.com\b'
    return set(re.findall(email_pattern, text, re.IGNORECASE))

def save_emails(emails, output_file='emails.txt'):
    try:
        unique_emails = sorted(set(emails))
        with open(output_file, 'a') as f:
            for email in unique_emails:
                f.write(email + '\n')
        logger.info(f"Saved {len(unique_emails)} unique emails to {output_file}")
    except Exception as e:
        logger.error(f"Error saving emails: {e}")

def perform_search(driver, name, domain, niche, page):
    query = f'"{name}" "{domain}" "{niche}"'
    encoded_query = urllib.parse.quote(query)
    start = (page - 1) * 10 + 1
    search_url = f"https://www.google.com/search?q={encoded_query}&start={start}"
    
    logger.info(f"Searching URL: {search_url}")
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
        return None
    
    return driver.page_source

def scrape_emails(driver, name, domain, niche, num_pages=5):
    logger.info(f"Scraping emails for {name} - {domain} - {niche}")
    collected_emails = set()
    
    for page in range(1, num_pages + 1):
        page_source = perform_search(driver, name, domain, niche, page)
        if page_source is None:
            continue
        
        emails = get_emails(page_source)
        logger.info(f"Found {len(emails)} emails on page {page} for {name} - {domain} - {niche}")
        collected_emails.update(emails)
        
        time.sleep(2)  # Wait between requests
    
    save_emails(collected_emails, f"emails_{name.replace(' ', '_')}_{domain}_{niche.replace(' ', '_')}.txt")
    logger.info(f"Finished scraping for {name} - {domain} - {niche}. Total emails collected: {len(collected_emails)}")
    return collected_emails

def main():
    config = load_config()
    names = [name.strip() for name in config['names'].split(',')]
    niches = [niche.strip() for niche in config['niche'].split(',')]
    domain = config['domain']
    
    driver = initialize_driver()
    all_emails = set()
    
    try:
        for name in names:
            for niche in niches:
                emails = scrape_emails(driver, name, domain, niche)
                all_emails.update(emails)
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
    finally:
        driver.quit()
    
    save_emails(all_emails, 'final_combined_emails.txt')
    logger.info("Scraping process completed")

if __name__ == "__main__":
    main()