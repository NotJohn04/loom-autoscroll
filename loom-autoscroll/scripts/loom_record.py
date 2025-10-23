from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, csv, os, random, pyautogui
import chromedriver_autoinstaller

# ---------- CONFIG ----------
PROFILE_ROOT     = r"C:\ChromeSelenium\AutomationProfile"   # non-default folder; log into Loom once here
CLIENTS_FILE     = os.path.abspath("../data/clients.csv")
OUTPUT_FILE      = os.path.abspath("../data/output.csv")
MP3_URL          = "https://loom-autoscroll.vercel.app/assets/intro-CO-cP7Qi.mp3"
RECORD_DURATION  = 97            # total run time (sec)
AUDIO_DELAY_SECS = 3             # wait after hotkey before playing mp3
SCROLL_DELAY_SECS= 6             # wait after hotkey before starting scroll
LOOM_HOTKEY      = ("ctrl", "shift", "l")   # Loom global hotkey

# ---------- DRIVER ----------
chromedriver_autoinstaller.install()
options = webdriver.ChromeOptions()
options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
options.add_argument(f"--user-data-dir={PROFILE_ROOT}")     # non-default data dir so Selenium can attach
options.add_argument("--start-maximized")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--autoplay-policy=no-user-gesture-required")
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
wait   = WebDriverWait(driver, 30)

# ---------- small helpers ----------
def wait_ready(drv, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if drv.execute_script("return document.readyState") == "complete":
                return True
        except Exception:
            pass
        time.sleep(0.1)
    return False

def focus_chrome():
    try: driver.maximize_window()
    except: pass
    pyautogui.moveTo(300, 200, duration=0.05)
    pyautogui.click()

def human_scroll(duration_sec):
    end = time.time() + duration_sec
    while time.time() < end:
        step = random.randint(120, 280)
        driver.execute_script(f"window.scrollBy(0, {step});")
        time.sleep(random.uniform(0.35, 0.8))
        if random.random() < 0.12:
            time.sleep(random.uniform(0.8, 1.6))

def open_latest_from_library_and_rename(new_title):
    # Go to your Library (all videos), click the newest card, then rename on the share page.
    driver.get("https://www.loom.com/looms/videos")
    wait_ready(driver)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-videoid]")))
    # first visible card link to /share/...
    cards = driver.find_elements(By.CSS_SELECTOR, "article[data-videoid] a[href*='/share/']")
    if not cards:
        # lazy-load fallback
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.4)
            cards = driver.find_elements(By.CSS_SELECTOR, "article[data-videoid] a[href*='/share/']")
            if cards: break
    if not cards:
        raise RuntimeError("No video cards found on Library page.")
    cards[0].click()

    wait.until(EC.url_contains("/share/"))
    wait_ready(driver)

    # Click the title container to activate editing, then type the new title
    # CSS from your screenshot:
    title_container_sel = "div.static-title_staticTitleEditableContainer_YeN"
    try:
        try:
            tc = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, title_container_sel))
            )
            tc.click()
        except Exception:
            pass  # sometimes already focused

        active = driver.switch_to.active_element
        active.send_keys(Keys.CONTROL, "a")
        active.send_keys(new_title)
        active.send_keys(Keys.ENTER)
        time.sleep(0.8)
    except Exception:
        # fallbacks
        for sel in [
            "h1[contenteditable='true']",
            "[data-testid='video-title']",
            "[role='textbox']",
        ]:
            try:
                el = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                el.click()
                el.send_keys(Keys.CONTROL, "a")
                el.send_keys(new_title)
                el.send_keys(Keys.ENTER)
                time.sleep(0.8)
                break
            except Exception:
                continue

    return driver.current_url

# ---------- main per-client flow ----------
def record_for_client(name, url):
    print(f"\n— {name} —")
    driver.get(url)
    wait_ready(driver)

    # Start Loom (desktop app/extension handles it)
    focus_chrome()
    pyautogui.hotkey(*LOOM_HOTKEY)
    print("🎥 Recording hotkey sent")

    start_ts = time.time()

    # Delay a bit, then play the mp3
    time.sleep(max(0, AUDIO_DELAY_SECS))
    driver.execute_script(f"""
        (function(){{
            try {{
                var a = document.createElement('audio');
                a.src = "{MP3_URL}";
                a.autoplay = true; a.volume = 1.0; a.style.display='none';
                document.body.appendChild(a);
                a.play().catch(()=>{{}});
            }} catch(e) {{}}
        }})();
    """)
    print("🎵 MP3 injected")

    # Wait until it's time to begin scrolling, then scroll for the remaining time
    now = time.time()
    delay_left = SCROLL_DELAY_SECS - (now - start_ts)
    if delay_left > 0:
        time.sleep(delay_left)

    remaining = max(2, RECORD_DURATION - (time.time() - start_ts))
    human_scroll(remaining)

    # Stop Loom
    focus_chrome()
    pyautogui.hotkey(*LOOM_HOTKEY)
    print("🛑 Stop hotkey sent")

    # Go to Library → open newest → rename → return share URL
    new_title = f"{name} | Solar Focus. No Risk Growth"
    try:
        share_url = open_latest_from_library_and_rename(new_title)
        print(f"🔗 Saved: {share_url}")
        return share_url
    except Exception as e:
        print("⚠️ Could not open/rename from Library:", e)
        return driver.current_url

# ---------- Runner ----------
def main():
    results = []
    with open(CLIENTS_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or row.get("Name") or "").strip()
            url  = (row.get("url")  or row.get("URL")  or "").strip()
            if not name or not url:
                print("⚠️ Skipping row (missing name/url):", row); continue
            link = record_for_client(name, url)
            results.append({"name": name, "url": url, "loom_url": link})
            # write incrementally so you don’t lose progress
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out:
                w = csv.DictWriter(out, fieldnames=["name", "url", "loom_url"])
                w.writeheader(); w.writerows(results)

    print("\n🎉 All recordings done and saved!\n")

if __name__ == "__main__":
    main()
