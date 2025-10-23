import time
import pickle
import os
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_FILE = "loom_cookies.pkl"
CLIENTS_FILE = "../data/clients.csv"   # adjust if path differs

def save_cookies(driver, path):
    with open(path, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

def load_cookies(driver, path):
    with open(path, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            if "expiry" in cookie:
                cookie["expiry"] = int(cookie["expiry"])
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠️ Skipped cookie {cookie.get('name')}: {e}")

def open_with_profile():
    options = webdriver.ChromeOptions()
    # load your actual Chrome profile so you stay logged in to Loom
    # options.add_argument(r"--user-data-dir=C:\Users\user\AppData\Local\Google\Chrome\User Data")
    # options.add_argument(r"--profile-directory=Default")
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--autoplay-policy=no-user-gesture-required")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.loom.com/")
    return driver

def click_start_record(driver):
    wait = WebDriverWait(driver, 30)
    record_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Start recording')]"))
    )
    record_button.click()
    print("🎥 Clicked 'Start recording'!")

def record_for_client(driver, name, url):
    print(f"🎯 Recording for {name} ({url})")
    driver.get("https://your-vercel-host/")  # <-- put your deployed Loom recorder URL
    input("⏸ Pre-record open. Press ENTER to start recording...")
    click_start_record(driver)

    # Now switch to client site
    driver.get(url)
    time.sleep(8)  # let it scroll or load

    # TODO: trigger stop recording via Selenium (ENTER key or SDK event)

def main():
    driver = open_with_profile()

    # if no cookies saved yet, log in manually once
    if not os.path.exists(COOKIE_FILE):
        input("👉 Please log in to Loom in the opened browser, then press ENTER...")
        save_cookies(driver, COOKIE_FILE)
    else:
        load_cookies(driver, COOKIE_FILE)
        driver.refresh()

    with open(CLIENTS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            record_for_client(driver, row["name"], row["url"])

    driver.quit()

if __name__ == "__main__":
    main()
