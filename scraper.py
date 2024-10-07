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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    print("Loading configuration...")
    config_path = 'config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("Configuration loaded successfully.")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
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
    logger.info(f"Saving {len(emails)} emails to {output_file}...")
    try:
        unique_emails = sorted(set(emails))
        with open(output_file, 'a') as f:  # Changed to append mode
            for email in unique_emails:
                f.write(email + '\n')
        logger.info(f"Saved {len(unique_emails)} unique emails successfully.")
    except Exception as e:
        logger.error(f"Error saving emails: {e}")

def perform_search(driver, query, start):
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.google.com/search?q={encoded_query}&start={start}"
    driver.get(search_url)
    print(f"Navigated to search URL: {search_url}")
    
    try:
        consent_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept all')]"))
        )
        consent_button.click()
        print("Accepted consent dialog")
    except TimeoutException:
        print("No consent dialog found or already accepted")
    
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        print("Search results loaded successfully")
    except TimeoutException:
        print("Timed out waiting for search results")
        raise

def scrape_emails(driver, query, num_pages=5):
    logger.info(f"Scraping emails for query: {query}")
    collected_emails = set()
    for page in range(num_pages):
        start = page * 10 + 1
        perform_search(driver, query, start)
        logger.info(f"Scraping page {page + 1}...")
        time.sleep(2)  # Wait for the page to load
        page_source = driver.page_source
        emails = get_emails(page_source)
        logger.info(f"Found {len(emails)} emails on page {page + 1}.")
        collected_emails.update(emails)
        
        # Save emails after each page to avoid data loss
        save_emails(collected_emails, f"emails_{query.replace(' ', '_')}.txt")
    
    logger.info(f"Total emails collected for query '{query}': {len(collected_emails)}")
    return collected_emails

def main():
    logger.info("Starting the scraper...")
    config = load_config()
    names = [name.strip() for name in config['names'].split(',')]
    niche = config['niche']
    domain = config['domain']
    
    driver = initialize_driver()
    
    all_emails = set()
    for name in names:
        query = f'"{name}" "{domain}" "{niche}"'
        try:
            emails = scrape_emails(driver, query)
            all_emails.update(emails)
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            continue  # Move to the next query
    
    driver.quit()
    logger.info("WebDriver closed.")
    
    # Combine all individual query results
    logger.info("Combining all email results...")
    combined_emails = set()
    for name in names:
        filename = f"emails_{name.replace(' ', '_')}_{domain}_{niche}.txt"
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                combined_emails.update(f.read().splitlines())
    
    # Save the final combined result
    save_emails(combined_emails, 'final_combined_emails.txt')
    logger.info("Scraper finished successfully.")

if __name__ == "__main__":
    main()