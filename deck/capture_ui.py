"""Capture the two product screenshots the deck embeds, from the running web UI.

    python -m agent.web           # shell 1: serves http://127.0.0.1:7000
    python deck/capture_ui.py     # shell 2: -> deck/assets/ui_full.png + ui_rejected.png

Uses the UI's instant SAMPLE replay, so the shots are deterministic and match the demo.
Needs: pip install playwright && python -m playwright install chromium
"""
import os

from playwright.sync_api import sync_playwright

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
URL = os.environ.get("UI_URL", "http://127.0.0.1:7000")


def main():
    os.makedirs(ASSETS, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1000}, device_scale_factor=2)
        page.goto(URL, wait_until="load")
        page.click("#replay")
        page.wait_for_selector(".card.bad", timeout=20000)
        page.wait_for_timeout(500)
        page.locator("#out").screenshot(path=os.path.join(ASSETS, "ui_full.png"))
        page.locator(".card.bad").screenshot(path=os.path.join(ASSETS, "ui_rejected.png"))
        browser.close()
    print("captured ->", ASSETS)


if __name__ == "__main__":
    main()
