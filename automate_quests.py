import os
import re
import sys
import time
import select
from playwright.sync_api import sync_playwright

def run_automation():
    user_data_dir = os.path.join(os.getcwd(), "browser_profile")
    
    quest_categories = [
        "https://club.nzxt.com/v2/nzxt-club-quests/daily-checkin",
        "https://club.nzxt.com/v2/nzxt-club-quests/x-twitter-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/facebook-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/instagram-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/tiktok-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/reddit-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/youtube-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/twitch-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/discord-quests"  # Discord last
    ]
    
    with sync_playwright() as p:
        print("Launching system Google Chrome...")
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            viewport={"width": 1510, "height": 1232},
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        
        print("Navigating to NZXT Club Login...")
        page.goto("https://club.nzxt.com/v2/onboarding/login")
        
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please log into your profile in the browser window.")
        print("Once you are logged in and looking at your dashboard,")
        print("come back here to the terminal and press ENTER to start automation.")
        print("="*50 + "\n")
        
        input("Press Enter here ONLY after you have finished logging in...")

        print("\n--- Automation Started ---")
        print("Press Ctrl + C in your terminal at any time to stop.\n")

        try:
            for cat_url in quest_categories:
                print(f"\nNavigating to category: {cat_url}")
                page.goto(cat_url)
                
                # Wait for hydration
                page.wait_for_timeout(3000)
                try:
                    page.wait_for_selector(".hv2-skeleton", state="detached", timeout=10000)
                except Exception:
                    pass

                is_discord = "discord-quests" in cat_url

                # Daily Check-in Logic
                if "daily-checkin" in cat_url:
                    print("Processing Daily Check-in button...")
                    try:
                        already_checked = page.locator("text=/Checked in for today/i").count() > 0
                        if already_checked:
                            print("Daily check-in already completed for today.")
                        else:
                            check_in_btn = page.locator("button, a").filter(has_text=re.compile(r"^check\s*in$", re.I)).first
                            if check_in_btn.is_visible():
                                check_in_btn.click()
                                print("Successfully clicked the 'Check in' button!")
                                page.wait_for_timeout(3000)
                            else:
                                print("No active 'Check in' button found.")
                    except Exception as e:
                        print(f"Skipped daily check-in interaction due to: {e}")
                    continue

                # Target URL quest links
                try:
                    page.wait_for_selector('a[href*="?d=quest:"]', timeout=10000)
                except Exception:
                    print("No quest links found on page.")
                    continue

                quest_links = page.locator('a[href*="?d=quest:"]').all()
                print(f"Found {len(quest_links)} total quest links on page.")

                unclaimed_count = 0
                for link in quest_links:
                    try:
                        # Check the ENTIRE parent card container for completion indicators
                        is_claimed = link.evaluate("""el => {
                            // Find parent container box (walk up parent nodes)
                            let card = el.closest('div[style*="border"], div[class*="card"], li, div[data-block-type]') || el.parentElement;
                            
                            if (!card) card = el;

                            // Check text content inside parent card
                            const cardText = (card.innerText || '').toUpperCase();
                            if (cardText.includes('CLAIMED')) return true;

                            // Check for checkmark icon anywhere inside parent card
                            const hasCheckIcon = card.querySelector('.fa-check, i[class*="check"], svg[class*="check"]') !== null;
                            if (hasCheckIcon) return true;

                            // Check circle styling for active accent background
                            const spans = Array.from(card.querySelectorAll('span'));
                            const hasAccentCircle = spans.some(s => s.getAttribute('style') && s.getAttribute('style').includes('var(--hv2-color-accent)'));
                            if (hasAccentCircle) return true;

                            return false;
                        }""")

                        if is_claimed:
                            continue

                        unclaimed_count += 1
                        href = link.get_attribute("href")
                        print(f"Opening unclaimed quest: {href}")

                        link.scroll_into_view_if_needed()
                        link.click()
                        page.wait_for_timeout(1500)

                        # Locate modal dialog
                        modal = page.locator('div[role="dialog"], [class*="modal"]')
                        if modal.is_visible():
                            if is_discord:
                                print("\n" + "!"*50)
                                print("DISCORD PUZZLE DETECTED: Type the answer in ALL CAPS and submit.")
                                print("Press ENTER here in the terminal once done, or wait up to 2 minutes.")
                                print("!"*50 + "\n")
                                
                                start_time = time.time()
                                timeout = 120
                                
                                if os.name == 'nt':
                                    import msvcrt
                                    while time.time() - start_time < timeout:
                                        if msvcrt.kbhit():
                                            if msvcrt.getch() in [b'\r', b'\n']:
                                                print("\nEnter pressed. Continuing workflow...")
                                                break
                                        time.sleep(0.1)
                                else:
                                    while time.time() - start_time < timeout:
                                        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                                        if rlist:
                                            sys.stdin.readline()
                                            print("\nEnter pressed. Continuing workflow...")
                                            break
                            else:
                                action_btn = modal.locator('a, button').filter(has_text=re.compile(r"open link|start|verify|claim", re.I)).first
                                if action_btn.is_visible():
                                    print("Clicking action button inside modal...")
                                    try:
                                        with browser_context.expect_page(timeout=4000) as new_page_info:
                                            action_btn.click()
                                        
                                        new_tab = new_page_info.value
                                        new_tab.wait_for_load_state()
                                        new_tab.close()
                                        print("Closed external tab.")
                                    except Exception:
                                        pass

                                page.wait_for_timeout(2000)

                            # Close modal
                            close_btn = modal.locator('button:has(.fa-xmark), button:has(.fa-times), button[aria-label="Close"], button.modal-close').first
                            if close_btn.is_visible():
                                close_btn.click()
                            else:
                                page.keyboard.press("Escape")
                            
                            page.wait_for_timeout(1000)

                    except Exception as e:
                        print(f"Error processing quest item: {e}")
                        continue

                if unclaimed_count == 0:
                    print("All quests in this category are already claimed.")

            print("\nAll categories processed successfully!")

        except KeyboardInterrupt:
            print("\n[Automation stopped safely by user via Ctrl + C]")
        finally:
            try:
                browser_context.close()
            except Exception:
                pass

if __name__ == "__main__":
    run_automation()
