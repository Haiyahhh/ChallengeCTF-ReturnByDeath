import sys
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

os.environ['TMPDIR'] = '/app/cache'
os.environ['SELENIUM_CACHE_PATH'] = '/app/cache/selenium-cache'
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
TARGET_HOST = "http://localhost:8080"

class AdminBot:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--user-data-dir=/app/cache/chrome-user-data")
        chrome_options.add_argument("--disable-crash-reporter")

        service = Service(
            executable_path="/usr/bin/chromedriver"
        )
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(10)

    def login_and_visit(self, url):
        print(f"[BOT] Admin process started. Target: {url}")
        
        try:
            session = requests.Session()
            login_resp = session.post(f"{TARGET_HOST}/api/v1/auth/login", json={
                "username": "admin",
                "password": ADMIN_PASSWORD
            })
            
            if login_resp.status_code != 200:
                print("[BOT] Failed to log in. Aborting.")
                return
                
            jwt_token = session.cookies.get('session_token')
        except Exception as e:
            print(f"[BOT] API Login error: {e}")
            return
            
        try:
            self.driver.get(TARGET_HOST)
            
            self.driver.add_cookie({
                'name': 'session_token',
                'value': jwt_token,
                'path': '/',
                'httponly': True
            })
            
            print("[BOT] Session established. Visiting payload URL...")
            self.driver.get(url)
            
            time.sleep(3) 
            
        except Exception as e:
            print(f"[BOT] Selenium Error: {e}")

    def close(self):
        self.driver.quit()
        print("[BOT] Admin process finished.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        bot = AdminBot()
        bot.login_and_visit(target_url)
        bot.close()