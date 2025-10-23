# final_loom_recorder.py  (updated)
from __future__ import annotations
import os, csv, time, random, re
import pyautogui, pyperclip

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import chromedriver_autoinstaller

# ------- OPTIONAL (better window close by title) -------
try:
    import pygetwindow as gw
except Exception:
    gw = None
# ------------------------------------------------------

# ===================== CONFIG =====================
PROFILE_ROOT = r"C:\ChromeSelenium\AutomationProfile"
CLIENTS_FILE = os.path.abspath("../data/clients.csv")
OUTPUT_FILE  = os.path.abspath("../data/output.csv")

MP3_URL      = "https://loom-autoscroll.vercel.app/assets/intro-CO-cP7Qi.mp3"
MP3_LENGTH   = 96            # seconds (your file is ~1:36)
COUNTDOWN    = 3             # Loom’s on-screen countdown
AUDIO_DELAY  = 6             # start MP3 6s after hotkey (i.e., 3s after the countdown)
SCROLL_DELAY = 8             # begin scrolling 8s after hotkey
TAIL_BUFFER  = 0             # stop ~2s after MP3 ends

# Total time FROM HOTKEY to STOP so that the video ends just after the MP3:
TOTAL_RECORD = COUNTDOWN + AUDIO_DELAY + MP3_LENGTH + TAIL_BUFFER

LOOM_HOTKEY  = ("ctrl", "shift", "l")   # make sure this matches Loom desktop

pyautogui.PAUSE = 0.03
pyautogui.FAILSAFE = False

def close_new_loom_windows(prev_titles:set[str], wait_seconds:float = 10.0) -> bool:
    """
    Close ONLY the brand-new Chrome window(s) that appeared after we stopped Loom.
    We identify them by: (a) not in prev_titles, and (b) ' - Google Chrome' in title.
    Returns True if at least one window was closed.
    """
    if not gw:
        # no module -> don't send Ctrl+W blindly anymore (can close terminal)
        return False

    deadline = time.time() + wait_seconds
    closed_any = False

    while time.time() < deadline:
        try:
            allwins = gw.getAllWindows()
        except Exception:
            time.sleep(0.2)
            continue

        # Titles that are new since we took the snapshot
        newwins = [w for w in allwins if (w.title or "").strip() and (w.title not in prev_titles)]

        # Prefer Chrome windows
        candidates = [w for w in newwins if " - Google Chrome" in (w.title or "")]
        if not candidates:
            candidates = newwins  # fallback: any new window

        did_close_this_round = False
        for w in candidates:
            try:
                # Bring it forward then close via OS (no keystrokes)
                try:
                    w.activate(); time.sleep(0.15)
                except Exception:
                    pass
                w.close()
                closed_any = True
                did_close_this_round = True
            except Exception:
                continue

        if did_close_this_round:
            time.sleep(0.4)
            break  # usually only one share window opens

        time.sleep(0.25)

    return closed_any

# ===================== DRIVER =====================
def make_driver() -> webdriver.Chrome:
    chromedriver_autoinstaller.install()
    opts = webdriver.ChromeOptions()
    opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    opts.add_argument(f"--user-data-dir={PROFILE_ROOT}")   # non-default dir
    opts.add_argument("--start-maximized")
    opts.add_argument("--autoplay-policy=no-user-gesture-required")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=opts)

driver = make_driver()
wait   = WebDriverWait(driver, 20)

# ===================== HELPERS =====================
def wait_ready(timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if driver.execute_script("return document.readyState") == "complete":
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
        try:
            driver.execute_script(f"window.scrollBy(0,{random.randint(120,280)});")
        except Exception:
            # If Selenium hiccups, just wait a tick and continue
            time.sleep(0.2)
        time.sleep(random.uniform(0.35, 0.8))
        if random.random() < 0.12:
            time.sleep(random.uniform(0.8, 1.6))

def inject_audio():
    driver.execute_script(f"""
        (function(){{
            try {{
                var a=document.createElement('audio');
                a.src="{MP3_URL}";
                a.autoplay=true; a.volume=1.0; a.style.display='none';
                document.body.appendChild(a);
                a.play().catch(()=>{{}});
            }} catch(e) {{}}
        }})();
    """)

def get_clipboard_loom_url(timeout=25) -> str|None:
    pat = re.compile(r"https://www\.loom\.com/share/[A-Za-z0-9]+")
    end = time.time() + timeout
    last = ""
    while time.time() < end:
        try:
            txt = pyperclip.paste().strip()
            if txt != last:
                last = txt
                m = pat.search(txt)
                if m:
                    return m.group(0)
        except Exception:
            pass
        time.sleep(0.3)
    return None

def close_loom_share_window():
    """Close the Loom share window that pops to the front after stopping."""
    time.sleep(0.7)
    # Prefer exact close by window title if pygetwindow is available
    if gw:
        try:
            for w in gw.getAllWindows():
                t = (w.title or "").lower()
                if "loom" in t or "loom.com" in t:
                    try:
                        w.activate(); time.sleep(0.15)
                    except Exception:
                        pass
                    try:
                        w.close()
                    except Exception:
                        pass
            time.sleep(0.3)
            return
        except Exception:
            pass
    # Fallback: send Ctrl+W a couple of times (closes the frontmost window)
    pyautogui.hotkey("ctrl", "w")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "w")

# ===================== CORE =====================
def record_for_client(name, url):
    print(f"\n— {name} —")
    driver.get(url); wait_ready()

    # Start recording
    focus_chrome()
    pyautogui.hotkey(*LOOM_HOTKEY)
    print("🎥 Recording hotkey sent")
    start = time.time()

    # Loom countdown
    time.sleep(COUNTDOWN)

    # Delay then inject MP3
    to_audio = AUDIO_DELAY - (time.time() - start)
    if to_audio > 0: time.sleep(to_audio)
    inject_audio()
    print("🎵 MP3 injected")

    # Delay then scroll until TOTAL_RECORD
    to_scroll = SCROLL_DELAY - (time.time() - start)
    if to_scroll > 0: time.sleep(to_scroll)
    remaining = max(2, TOTAL_RECORD - (time.time() - start))
    human_scroll(remaining)

    # Snapshot OS windows BEFORE stopping (so we can detect the new share window)
    prev_titles = set()
    if gw:
        try:
            prev_titles = { (w.title or "").strip() for w in gw.getAllWindows() }
        except Exception:
            prev_titles = set()

    # Stop recording
    focus_chrome()
    pyautogui.hotkey(*LOOM_HOTKEY)
    print("🛑 Stop hotkey sent")

    # Close the brand-new Loom share window(s) so they don't block the next run
    closed = close_new_loom_windows(prev_titles)
    if closed:
        # Refocus our controlled Chrome window
        focus_chrome()

    # Get share link from clipboard
    link = get_clipboard_loom_url(timeout=25)
    if not link:
        print("⚠️ No Loom URL picked from clipboard. Using current page as fallback.")
        link = url
    print(f"🔗 {link}")
    return link

def main():
    if not os.path.exists(CLIENTS_FILE):
        raise FileNotFoundError(f"Missing clients file: {CLIENTS_FILE}")

    results = []
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(CLIENTS_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or row.get("Name") or "").strip()
            url  = (row.get("url")  or row.get("URL")  or "").strip()
            if not name or not url:
                print("⚠️ Skipping row with missing name/url:", row)
                continue

            link = record_for_client(name, url)
            results.append({"name": name, "url": url, "loom_url": link})

            # Save progress after each client
            with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as out:
                w = csv.DictWriter(out, fieldnames=["name", "url", "loom_url"])
                w.writeheader(); w.writerows(results)

    print("\n🎉 Done!\n")

if __name__ == "__main__":
    try:
        main()
    finally:
        try: driver.quit()
        except: pass
