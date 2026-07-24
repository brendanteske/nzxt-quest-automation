import os
import time
import sys
import select
from playwright.sync_api import sync_playwright

def run_automation():
    user_data_dir = os.path.join(os.getcwd(), "browser_profile")
    
    # Categories with Discord placed last
    quest_categories = [
        "https://club.nzxt.com/modules/2972",
        "https://club.nzxt.com/modules/x-quests",
        "https://club.nzxt.com/modules/facebook-quests",
        "https://club.nzxt.com/modules/instagram-quests",
        "https://club.nzxt.com/modules/tiktok-quests",
        "https://club.nzxt.com/modules/reddit-quests",
        "https://club.nzxt.com/modules/youtube-quests",
        "https://club.nzxt.com/modules/twitch-quests",
        "https://club.nzxt.com/modules/discord-quests"  # Discord last
    ]
    
    with sync_playwright() as p:
        print("Launching system Google Chrome...")
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            viewport={"width": 1510, "height": 1232}
        )
        
        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        
        print("Navigating to NZXT Club...")
        page.goto("https://club.nzxt.com/")
        
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please log into your profile in the browser window.")
        print("Once you are logged in and looking at your dashboard,")
        print("come back here to the terminal and press ENTER to start automation.")
        print("="*50 + "\n")
        
        input("Press Enter here ONLY after you have finished logging in...")

        print("\n--- Automation Started ---")
        print("Press Ctrl + C in your terminal at any time to stop.\n")

        try:
            # Click the main "NZXT Quests" sidebar button first
            print("Looking for 'NZXT Quests' sidebar button...")
            nzxt_quests_btn = page.locator("button", has_text="NZXT Quests")
            if nzxt_quests_btn.count() > 0 and nzxt_quests_btn.first.is_visible():
                nzxt_quests_btn.first.click(force=True)
                print("Clicked NZXT Quests button successfully!")
                page.wait_for_timeout(3000)
            else:
                print("Could not find NZXT Quests button directly, proceeding to category URLs...")

            # Cycle through each category link
            for cat_url in quest_categories:
                print(f"\nNavigating to category: {cat_url}")
                page.goto(cat_url)
                page.wait_for_timeout(3000)

                is_discord = "discord-quests" in cat_url

                # Special handling for Daily Check-in calendar view (modules/2972)
                if "2972" in cat_url:
                    print("Processing Daily Check-in calendar days...")
                    try:
                        claimed_daily = page.evaluate("""() => {
                            const dayCards = Array.from(document.querySelectorAll('div, button'));
                            const todayButton = dayCards.find(el => {
                                const text = (el.innerText || '').toLowerCase();
                                return el.tagName === 'BUTTON' && text.includes('✓') == false && text.includes('🔒') == false;
                            });
                            
                            if (todayButton) {
                                todayButton.click();
                                return true;
                            }
                            return false;
                        }""")
                        if claimed_daily:
                            print("Successfully claimed today's daily check-in!")
                            page.wait_for_timeout(3000)
                        else:
                            print("No claimable daily check-in button available today.")
                    except Exception as e:
                        print(f"Skipped daily check-in interaction due to: {e}")
                    continue

                # Standard Quest Category Processing Loop
                while True:
                    page.wait_for_timeout(2000)

                    start_buttons = page.locator("button", has_text="Start Quest")
                    claim_check = page.locator("button, a, div", has_text="Claim Reward")
                    
                    if start_buttons.count() == 0 and claim_check.count() == 0:
                        break

                    # Click Start Quest if available
                    if start_buttons.count() > 0 and start_buttons.first.is_visible():
                        print("Clicking Start Quest...")
                        start_buttons.first.click()
                        page.wait_for_timeout(3000)

                    # If this is Discord, handle puzzle input with 2-minute timer or early Enter press
                    if is_discord:
                        print("\n" + "!"*50)
                        print("DISCORD PUZZLE DETECTED: Type the answer in ALL CAPS and submit.")
                        print("Press ENTER here in the terminal once done, or wait up to 2 minutes.")
                        print("!"*50 + "\n")
                        
                        start_time = time.time()
                        timeout = 120
                        
                        if os.name == 'nt':
                            # Windows non-blocking input check approach
                            import msvcrt
                            while time.time() - start_time < timeout:
                                if msvcrt.kbhit():
                                    if msvcrt.getch() in [b'\r', b'\n']:
                                        print("\nEnter pressed. Continuing workflow...")
                                        break
                                time.sleep(0.1)
                        else:
                            # Unix select-based input check approach
                            while time.time() - start_time < timeout:
                                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                                if rlist:
                                    sys.stdin.readline()
                                    print("\nEnter pressed. Continuing workflow...")
                                    break
                    else:
                        # Standard External Link Handling for other categories
                        print("Looking for external link button...")
                        link_clicked = False
                        for _ in range(10):
                            link_element = page.locator("a, button, [role='button']", has_text="Click the link")
                            if link_element.count() > 0 and link_element.first.is_visible():
                                try:
                                    link_element.first.click()
                                    print("Successfully clicked external link!")
                                    link_clicked = True
                                    break
                                except Exception:
                                    pass
                            page.wait_for_timeout(1000)
                        
                        if link_clicked:
                            page.wait_for_timeout(4000)
                            if len(browser_context.pages) > 1:
                                for extra_page in browser_context.pages[1:]:
                                    try:
                                        extra_page.close()
                                    except Exception:
                                        pass
                                print("Extra tabs closed.")

                    page.wait_for_timeout(2000)
                    page.reload()
                    page.wait_for_timeout(3000)

                    # Find and Click Claim Reward
                    print("Waiting for Claim Reward button...")
                    claimed = False
                    for _ in range(20):
                        try:
                            claimed = page.evaluate("""() => {
                                const elements = Array.from(document.querySelectorAll('button, div, span, a'));
                                const target = elements.find(el => 
                                    el.innerText && 
                                    el.innerText.trim().toLowerCase() === 'claim reward' && 
                                    el.offsetParent !== null
                                );
                                if (target) {
                                    target.click();
                                    target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                    return true;
                                }
                                return false;
                            }""")

                            if claimed:
                                print("Successfully triggered Claim Reward via direct DOM execution!")
                                break
                        except Exception:
                            pass
                        page.wait_for_timeout(1000)

                    if claimed:
                        page.wait_for_timeout(4000)

                    # Close Popup Modal
                    print("Looking for modal close button...")
                    for _ in range(6):
                        close_btn = page.locator("button.modal-close")
                        if close_btn.count() > 0 and close_btn.first.is_visible():
                            try:
                                close_btn.first.click(force=True)
                                print("Modal successfully closed via button.modal-close!")
                                page.wait_for_timeout(3000) 
                                break
                            except Exception:
                                pass
                        page.wait_for_timeout(1000)

                    break # Move to next category after finishing current items

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