from playwright.sync_api import sync_playwright
import time, os, csv

PROFILE_DIR = os.path.expanduser(r"~\\playwright_looom_profile")
CLIENTS_FILE = "../data/clients.csv"
OUTPUT_FILE = "../data/output.csv"

RECORD_DURATION = 97  # 1 min 37 sec

def smooth_scroll(page, duration=20, step=150):
    interval = 0.5
    ticks = int(duration / interval)
    for _ in range(ticks):
        page.evaluate(f"window.scrollBy(0, {step});")
        time.sleep(interval)

def record_for_client(control, browser, name, url):
    # 1. Click SDK
    time.sleep(5)
    control.wait_for_selector("#loom-record-sdk-button", timeout=15000)
    control.click("#loom-record-sdk-button")
    print(f"✅ Clicked SDK button for {name}")
    time.sleep(5)

    # 2. Wait for manual confirmation
    input("👉 Press ENTER to start recording...")

    # 3. Click Loom recorder "Start recording" button in shadow root
    overlay = control.wait_for_selector(
        "div#loom-sdk-record-overlay-shadow-root-id",
        state="attached",
        timeout=20000
    )
    shadow = overlay.evaluate_handle("el => el.shadowRoot")

    # Find ONLY the button that says "Start recording"
    start_btn = shadow.evaluate_handle("""
        root => [...root.querySelectorAll('button[data-qa="recorder-button"]')]
                .find(b => b.innerText.includes("Start recording"))
    """)
    start_btn.click()
    print("🎥 Start recording button clicked...")
    time.sleep(3)

    # 4. Open client site in new tab
    client = browser.new_page()
    client.goto(url)
    time.sleep(2)

    # 5. Inject intro.mp3 (from hosted Vercel path)
    client.evaluate("""
        var audio = document.createElement('audio');
        audio.src = 'https://loom-autoscroll.vercel.app/assets/intro-CO-cP7Qi.mp3';
        audio.autoplay = true;
        audio.volume = 1.0;
        document.body.appendChild(audio);
        audio.play().catch(e => console.log("Autoplay blocked:", e));
    """)
    print("🎵 intro.mp3 injected & playing...")

    # 6. Smooth scroll
    smooth_scroll(client, duration=RECORD_DURATION, step=150)

    # 7. Stop recording
    overlay = control.query_selector("div#loom-sdk-record-overlay-shadow-root-id")
    shadow = overlay.evaluate_handle("el => el.shadowRoot")
    stop_btn = shadow.evaluate_handle(
        "root => root.querySelector('button[data-qa=\"recorder-button\"]')"
    )
    stop_btn.click()
    print("🛑 Recording stopped.")

    # 8. Fake Loom URL (replace with real fetch later)
    return "https://loom.com/fake_video_url_" + name


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            args=[
                "--use-fake-ui-for-media-stream",
                "--autoplay-policy=no-user-gesture-required"
            ]
        )
        control = browser.new_page()
        control.goto("https://loom-autoscroll.vercel.app/")

        results = []
        with open(CLIENTS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                loom_url = record_for_client(control, browser, row["name"], row["url"])
                results.append({
                    "name": row["name"],
                    "url": row["url"],
                    "loom_url": loom_url
                })

        # Write to output.csv
        with open(OUTPUT_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "url", "loom_url"])
            writer.writeheader()
            writer.writerows(results)

        browser.close()

if __name__ == "__main__":
    main()
