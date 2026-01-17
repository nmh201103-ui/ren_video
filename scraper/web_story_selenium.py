"""Web Story Scraper with JavaScript support using Selenium"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def scrape_with_selenium(url: str, timeout=20):
    """Scrape JavaScript-heavy websites using Selenium"""
    from utils.logger import get_logger
    logger = get_logger()
    
    logger.info(f"🤖 Using Selenium to scrape JS content...")
    
    # Chrome options
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Headless mode (no GUI)
    if not os.getenv("SELENIUM_GUI"):
        options.add_argument("--headless")
    
    try:
        # Initialize driver
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(timeout)
        
        # Load page
        logger.info(f"⏳ Loading {url}...")
        driver.get(url)
        
        # Wait for content to load (try multiple selectors)
        selectors = [
            'article',
            '.article-detail',
            '.story-content',
            '[role="main"]',
            '.content',
            'body'
        ]
        
        content_found = False
        for selector in selectors:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.info(f"✅ Content loaded: {selector}")
                content_found = True
                break
            except:
                continue
        
        if not content_found:
            logger.warning("⚠️ Could not detect content load")
        
        # Give JS time to fully render
        time.sleep(2)
        
        # Get rendered HTML
        html = driver.page_source
        driver.quit()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        return soup
        
    except Exception as e:
        logger.error(f"❌ Selenium failed: {e}")
        return None
