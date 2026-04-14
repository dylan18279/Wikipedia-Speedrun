from playwright.sync_api import sync_playwright
from logic import get_shortest_path
import time

# --- CONFIG ---
START_PAGE = "Pizza farm"
TARGET_PAGE = "Cristiano ronaldo"

def run_speedrun():
    # 1. THE THINKING PHASE
    print(f"🧠 AI is calculating the path from '{START_PAGE}' to '{TARGET_PAGE}'...")
    start_time = time.time()
    
    path = get_shortest_path(START_PAGE, TARGET_PAGE)
    
    if not path:
        print("❌ AI failed to find a path. Try increasing the scan limits in logic.py.")
        return

    duration = time.time() - start_time
    print(f"✅ Path Found in {duration:.2f}s: {' -> '.join(path)}")

    # 2. THE ACTION PHASE
    print("🚀 Launching Browser...")
    with sync_playwright() as p:
        # headless=False lets us watch the bot work
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Build the starting URL
        current_url = f"https://en.wikipedia.org/wiki/{path[0].replace(' ', '_')}"
        page.goto(current_url)

        # Loop through the path (skipping the first one since we're already there)
        for step in path[1:]:
            print(f"🖱️ Clicking: {step}")
            try:
                # Optimized Selector: Looks for the exact link in the main content area
                # This is much faster than scanning the whole page
                link_selector = f'#mw-content-text a[title="{step}"]'
                
                # Wait up to 5 seconds for the link to appear
                page.wait_for_selector(link_selector, timeout=5000)
                page.click(link_selector)
                
                # Wait for the next page to load its basic structure
                page.wait_for_load_state("domcontentloaded")
            except Exception:
                # Teleport Failsafe: If the link is hidden or in a weird menu
                print(f"⚠️ Link '{step}' not clickable. Teleporting to avoid lag...")
                page.goto(f"https://en.wikipedia.org/wiki/{step.replace(' ', '_')}")

        print("🏁 VICTORY REACHED!")
        time.sleep(5)  # Pause to see the target page
        browser.close()

if __name__ == "__main__":
    run_speedrun()