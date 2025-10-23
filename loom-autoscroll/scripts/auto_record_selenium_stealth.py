from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = webdriver.ChromeOptions()
# don't use your main profile to start with — test with no profile first
# options.add_argument(r"--user-data-dir=C:\path\to\clean_profile")  # optional if you have a safe profile
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--use-fake-ui-for-media-stream")
options.add_argument("--autoplay-policy=no-user-gesture-required")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# remove the "Chrome is being controlled by automated test software" banner via CDP:
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.navigator.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
    """
})

driver.get("https://accounts.google.com/")  # test google (expect likely blocked still)
time.sleep(5)

# Example to click Loom once you're logged in:
driver.get("https://your-vercel-host/")
wait = WebDriverWait(driver, 15)
btn = wait.until(EC.element_to_be_clickable((By.ID, "loom-record-sdk-button")))
btn.click()
print("Clicked Loom button")
time.sleep(10)
driver.quit()
