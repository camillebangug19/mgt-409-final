from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("/Users/camillebangug/projects/AI Foundations for Managers/Final AI Project Oct 25/docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
errors = []
ANSWERS = ["2", "Adult", "Older adult (65+)", "Cane or walker", "Oxygen", "Yes, one person",
           "No pets", "32399", "FL", "Apartment", "No"]

def idle(page, timeout=180000):
    """Wait until the bot has finished thinking."""
    page.wait_for_function("() => !document.querySelector('.typing')", timeout=timeout)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 430, "height": 920}, device_scale_factor=2)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" else None)

    page.goto("http://localhost:8000", wait_until="networkidle")
    page.screenshot(path=OUT/"1-landing.png", full_page=True)
    print("1 landing", flush=True)

    page.click("text=Start")
    idle(page)

    for i in range(40):
        # The chat unmounts the moment the survey is done, before the score
        # has loaded, so check for the input rather than for the score.
        if page.locator(".composer input").count() == 0:
            break
        msg = ANSWERS[i] if i < len(ANSWERS) else ("Yes" if i % 3 else "Partly")
        if i == 5:
            page.screenshot(path=OUT/"2-survey-chat.png", full_page=True)
            print("2 survey chat", flush=True)
        page.fill(".composer input", msg)
        page.click(".composer button[type=submit]")
        idle(page)
        print(f"   turn {i+1}: {msg}", flush=True)

    page.wait_for_selector(".bag-score", timeout=180000)
    page.wait_for_timeout(2000)
    page.screenshot(path=OUT/"3-score-reveal.png", full_page=True)
    print("3 score reveal:", page.locator(".bag-score").inner_text().replace("\n"," "),
          "|", page.locator(".bag-label").inner_text(), flush=True)
    print("   steps:", page.locator(".step-card h3").all_inner_texts(), flush=True)
    print("   gains:", page.locator(".gain").all_inner_texts(), flush=True)

    page.locator(".step-card").first.scroll_into_view_if_needed()
    page.screenshot(path=OUT/"4-next-steps.png", full_page=True)
    print("4 next steps", flush=True)

    first = page.locator(".step-card").first
    first.locator("button", has_text="I did this").click()
    page.wait_for_selector(".self-check input")
    for cb in first.locator(".self-check input").all():
        cb.check()
    page.screenshot(path=OUT/"5-self-check.png", full_page=True)
    print("5 self check", flush=True)

    first.locator("button", has_text="Confirm").click()
    page.wait_for_timeout(4000)
    page.screenshot(path=OUT/"6-score-up.png", full_page=True)
    print("6 score after:", page.locator(".bag-score").inner_text().replace("\n"," "),
          "|", page.locator(".bag-label").inner_text(), flush=True)
    print("   new steps:", page.locator(".step-card h3").all_inner_texts(), flush=True)
    b.close()

print("\nJS errors:", errors or "none")
for f in sorted(OUT.glob("*.png")): print(" ", f.name, f.stat().st_size//1024, "KB")
