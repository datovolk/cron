from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os

def get_driver(user_agent=None, headless=True):
    if user_agent is None:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"  # <== ВАЖНО!
    
    if headless:
        options.add_argument('--headless')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={user_agent}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.abspath(os.path.join(base_dir, "chromedriver"))
    service = Service(driver_path)

    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    return driver
