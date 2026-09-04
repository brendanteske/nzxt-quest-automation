import os
import sys
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_PATH = os.path.join(BASE_DIR, "script.log")
LOG_INFO_PATH = os.path.join(BASE_DIR, "log_info.json")
USER_DATA_DIR = os.path.join(BASE_DIR, "browser_profile")

DEFAULT_CONFIG = {
    "discord_webhook_url": "",
    "account_email": "",
    "account_password": "",
    "gmail_app_password": "",
    "email_sender_filter": "do-not-reply@club.nzxt.com",
    "headless_mode": False,
    "login_timeout_minutes": 5,
    "dependencies_installed": False
}

def setup_weekly_logger():
    """Manages a rotating log file that resets automatically every 7 days."""
    import time
    current_time = time.time()
    one_week_seconds = 7 * 24 * 60 * 60

    should_reset = False

    if os.path.exists(LOG_INFO_PATH):
        try:
            with open(LOG_INFO_PATH, "r", encoding="utf-8") as f:
                info = json.load(f)
                start_time = info.get("created_at", 0)
                if current_time - start_time >= one_week_seconds:
                    should_reset = True
        except Exception:
            should_reset = True
    else:
        should_reset = True

    if should_reset or not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write("--- LOG FILE INITIALIZED (Weekly Auto-Reset Active) ---\n")
        with open(LOG_INFO_PATH, "w", encoding="utf-8") as f:
            json.dump({"created_at": current_time}, f, indent=4)

    class Logger(object):
        def __init__(self):
            self.terminal = sys.stdout
            self.log = open(LOG_PATH, "a", encoding="utf-8")

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger()
    sys.stderr = Logger()

def load_or_create_config():
    """Generates config.json if missing, or loads existing configuration."""
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            print(f"[Config] Created new configuration file at: {CONFIG_PATH}")
        except Exception as e:
            print(f"[Config] Warning: Could not create config.json: {e}")
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            for key, val in DEFAULT_CONFIG.items():
                config.setdefault(key, val)
            return config
    except Exception as e:
        print(f"[Config] Warning: Failed to read config.json, using defaults: {e}")
        return DEFAULT_CONFIG

def update_config_key(key, value):
    """Updates a specific key in config.json and saves to disk."""
    config = load_or_create_config()
    config[key] = value
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[Config] Warning: Failed to update {key} in config.json: {e}")

def verify_and_install_dependencies():
    """Checks dependencies and installs missing ones if dependencies_installed is False."""
    config = load_or_create_config()
    
    if config.get("dependencies_installed", False):
        return

    print("[Setup] Checking required dependencies...")
    required_packages = {
        "playwright": "playwright",
        "bs4": "beautifulsoup4"
    }

    missing_packages = []
    for module_name, pip_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(pip_name)

    if missing_packages:
        print(f"[Setup] Missing packages detected: {', '.join(missing_packages)}")
        print("[Setup] Installing missing requirements...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            print("[Setup] Successfully installed required packages.")
        except Exception as e:
            print(f"[Setup] Error installing packages via pip: {e}")
            sys.exit(1)

    try:
        import playwright
        print("[Setup] Ensuring Playwright Chrome browser components are installed...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    except Exception as e:
        print(f"[Setup] Warning during Playwright installation check: {e}")

    update_config_key("dependencies_installed", True)
    print("[Setup] Dependency verification complete. Set dependencies_installed to True in config.json.")

# Initialize weekly logging system and dependencies
setup_weekly_logger()
verify_and_install_dependencies()

# Standard Library & Third-Party Imports
import re
import time
import imaplib
import email
import urllib.request
import bs4
from playwright.sync_api import sync_playwright

def send_discord_alert(webhook_url, title, description):
    """Sends a formatted notification embed to the configured Discord Webhook."""
    if not webhook_url or not webhook_url.startswith("http"):
        return

    payload = {
        "username": "NZXT Quest Bot",
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": 15158332,
                "footer": {"text": "NZXT Club Automation Alert"}
            }
        ]
    }

    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"[Discord] Failed to send webhook alert: {e}")

def fetch_latest_verification_code(gmail_address, app_password, sender_filter="do-not-reply@club.nzxt.com"):
    """Connects to Gmail via IMAP, finds the latest email from NZXT, and extracts the 6-digit verification code."""
    if not gmail_address or not app_password:
        print("[Gmail] Missing Gmail credentials in config.json.")
        return None

    try:
        print(f"[Gmail] Connecting to Gmail IMAP to check emails from {sender_filter}...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_address, app_password.replace(" ", ""))
        mail.select("inbox")

        status, messages = mail.search(None, f'FROM "{sender_filter}"')
        if status != "OK" or not messages[0]:
            status, messages = mail.search(None, 'FROM "club.nzxt.com"')

        mail_ids = messages[0].split()
        if not mail_ids:
            print("[Gmail] No emails found matching NZXT sender address.")
            mail.logout()
            return None

        latest_email_id = mail_ids[-1]
        _, msg_data = mail.fetch(latest_email_id, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                html_body = ""
                text_body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if "attachment" not in content_disposition:
                            if content_type == "text/html":
                                html_body += part.get_payload(decode=True).decode(errors="ignore")
                            elif content_type == "text/plain":
                                text_body += part.get_payload(decode=True).decode(errors="ignore")
                else:
                    html_body = msg.get_payload(decode=True).decode(errors="ignore")

                full_body = html_body or text_body

                if html_body:
                    soup = bs4.BeautifulSoup(html_body, "html.parser")
                    for p_tag in soup.find_all(["p", "div", "td", "span"]):
                        text = p_tag.get_text(strip=True)
                        if text.isdigit() and len(text) == 6:
                            print(f"[Gmail] Successfully parsed code via HTML element: {text}")
                            mail.logout()
                            return text

                code_match_context = re.search(r'verification code is:\s*.*?(\d{6})', full_body, re.I | re.DOTALL)
                if code_match_context:
                    code = code_match_context.group(1)
                    print(f"[Gmail] Successfully extracted code via contextual regex: {code}")
                    mail.logout()
                    return code

                code_match_fallback = re.search(r'\b(\d{6})\b', full_body)
                if code_match_fallback:
                    code = code_match_fallback.group(1)
                    print(f"[Gmail] Extracted 6-digit code via fallback: {code}")
                    mail.logout()
                    return code

        mail.logout()
    except Exception as e:
        print(f"[Gmail] Error retrieving code from Gmail: {e}")

    return None


def handle_verification_code(page, config):
    """Attempts to auto-fetch code from Gmail and enter it across the 6 split digit input fields."""
    gmail_addr = config.get("account_email", "")
    app_pass = config.get("gmail_app_password", "")
    sender_filter = config.get("email_sender_filter", "do-not-reply@club.nzxt.com")

    if not app_pass:
        print("[Verification] No Gmail App Password provided. Cannot fetch code automatically.")
        return False

    # Updated delay: wait 15 seconds for the email to arrive
    print("[Verification] Waiting 15 seconds for verification email to arrive...")
    page.wait_for_timeout(15000)

    code = fetch_latest_verification_code(gmail_addr, app_pass, sender_filter)
    if not code:
        print("[Verification] Retrying Gmail fetch after 5 seconds...")
        page.wait_for_timeout(5000)
        code = fetch_latest_verification_code(gmail_addr, app_pass, sender_filter)

    if code and len(code) == 6:
        try:
            print(f"[Verification] Auto-filling 6-digit code: {code}")
            
            # Check for the split multi-input digit fields
            digit_inputs = page.locator('input[aria-label^="Digit "]').all()
            
            if len(digit_inputs) >= 6:
                for idx, digit in enumerate(code):
                    digit_inputs[idx].focus()
                    digit_inputs[idx].fill(digit, force=True)
                    page.wait_for_timeout(100)
            else:
                # Strategy B: Fallback to single code input field if layout differs
                code_input = page.locator('input[name*="code" i], input[placeholder*="code" i], input[type="text"]').first
                if code_input.is_visible():
                    code_input.fill(code, force=True)

            page.wait_for_timeout(1000)

            # Click verification submission button if present
            verify_btn = page.locator('button:has-text("Verify"), button:has-text("Submit"), button[type="submit"]').first
            if verify_btn.is_visible() and verify_btn.is_enabled():
                verify_btn.click(force=True)
                print("[Verification] Submitted code. Waiting for session response...")
                page.wait_for_timeout(4000)
                return True

        except Exception as e:
            print(f"[Verification] Failed to fill code into page: {e}")

    return False


def attempt_login_page(page, email_addr, password):
    """Fills email, triggers ALTCHA captcha, clicks Continue with retry double-checks, and submits password."""
    if not email_addr or not password:
        print("[Auto-Login] Missing email or password in config.json. Automatic login skipped.")
        return False

    print("[Auto-Login] Processing login flow on onboarding page...")
    try:
        email_input = page.locator('input[name="email"]').first
        
        if not email_input.is_visible():
            email_input = page.locator('input[type="email"]').first

        if email_input.is_visible():
            print(f"[Auto-Login] Entering email address: {email_addr}")
            email_input.scroll_into_view_if_needed()
            email_input.focus()
            email_input.fill(email_addr, force=True)
            page.wait_for_timeout(1000)

            print("[Auto-Login] Interacting with ALTCHA verification widget...")
            altcha_handled = False

            try:
                page.evaluate("""() => {
                    const cb = document.querySelector('#altcha_checkbox') || 
                               document.querySelector('altcha-widget input[type="checkbox"]') ||
                               document.querySelector('input[id*="altcha"]');
                    if (cb) {
                        cb.scrollIntoView();
                        cb.click();
                        cb.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }""")
                altcha_handled = True
            except Exception as err:
                print(f"[Auto-Login] JS evaluation for ALTCHA failed: {err}")

            if not altcha_handled:
                altcha_loc = page.locator('#altcha_checkbox, altcha-widget input[type="checkbox"]').first
                if altcha_loc.count() > 0:
                    altcha_loc.click(force=True)

            print("[Auto-Login] Waiting for ALTCHA verification to complete (Continue button to enable)...")
            continue_btn = page.locator('button[data-element-key="btn-primary:0"], button[type="submit"]').first

            start_check = time.time()
            while time.time() - start_check < 30:
                if continue_btn.is_enabled():
                    print("[Auto-Login] Verification complete! Continue button enabled.")
                    break
                page.wait_for_timeout(1000)

            if continue_btn.is_enabled():
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    print(f"[Auto-Login] Attempt {attempt}/{max_retries}: Clicked Continue button.")
                    continue_btn.click(force=True)
                    
                    # Wait 8 seconds to allow request processing / page transition
                    print("[Auto-Login] Double checking if email field is cleared or 2FA/Password prompt appeared...")
                    page.wait_for_timeout(8000)

                    # Indicators that the continue button succeeded:
                    # 1. Email input is no longer visible
                    # 2. Password input is visible
                    # 3. 2FA verification prompt text or digit inputs appear
                    pass_visible = page.locator('input[type="password"], input[name="password"]').first.is_visible()
                    digit_visible = page.locator('input[aria-label^="Digit "]').first.is_visible()
                    verification_text = page.locator("text=/verify|code|sent an email|check your email/i").count() > 0
                    email_still_visible = page.locator('input[type="email"], input[name="email"]').first.is_visible()

                    if pass_visible or digit_visible or verification_text or not email_still_visible:
                        print("[Auto-Login] Success: Navigation progressed past email stage.")
                        break
                    else:
                        print("[Auto-Login] Email field is still showing. Continue click may have been rate-limited or dropped.")
                        if attempt < max_retries:
                            print("[Auto-Login] Retrying Continue button click after short pause...")
                            page.wait_for_timeout(2000)
            else:
                print("[Auto-Login] Warning: Continue button was not enabled within timeout.")

            # Proceed to Password input if present
            pass_input = page.locator('input[type="password"], input[name="password"]').first
            if pass_input.is_visible():
                print("[Auto-Login] Entering password...")
                pass_input.fill(password, force=True)
                page.wait_for_timeout(500)

                submit_btn = page.locator('button[type="submit"]').first
                if submit_btn.is_visible():
                    submit_btn.click(force=True)
                    print("[Auto-Login] Clicked final submit button.")
                    page.wait_for_timeout(4000)
                    return True

    except Exception as e:
        print(f"[Auto-Login] Exception during login sequence: {e}")

    return False


def verify_session_authentication(page, config):
    """Directly navigates to the login page and verifies or performs login."""
    webhook_url = config.get("discord_webhook_url", "").strip()
    account_email = config.get("account_email", "").strip()
    account_password = config.get("account_password", "").strip()
    timeout_mins = config.get("login_timeout_minutes", 5)

    print("Navigating directly to login page to verify session status...")
    page.goto("https://club.nzxt.com/v2/onboarding/login")
    page.wait_for_timeout(3000)

    # Check if we are actually on a login page by looking for the email input field
    has_email_field = page.locator('input[type="email"], input[name="email"]').count() > 0
    is_onboarding_url = "onboarding" in page.url.lower() or "login" in page.url.lower()

    if is_onboarding_url and has_email_field:
        print("[Auth Check] Unauthenticated state confirmed. Executing auto-login...")
        attempt_login_page(page, account_email, account_password)
    else:
        print("[Auth Check] Already authenticated! Session cookie/profile is active.")
        return

    # Check for 2FA / email verification code prompt
    needs_verification = page.locator("text=/verify|code|sent an email|check your email/i").count() > 0
    if needs_verification:
        print("[Authentication] Email verification prompt detected.")
        handle_verification_code(page, config)

    # Check if still stuck on login or verification
    still_email_field = page.locator('input[type="email"], input[name="email"]').count() > 0
    still_verification = page.locator("text=/verify|code|sent an email|check your email/i").count() > 0

    if still_email_field or still_verification or "login" in page.url.lower():
        print("\n" + "!"*60)
        print("MANUAL INTERVENTION REQUIRED: Automated login or verification incomplete.")
        print("!"*60 + "\n")
        
        send_discord_alert(
            webhook_url,
            "⚠️ NZXT Verification Required",
            f"Auto-login failed or captcha/2FA required. Please complete login manually. Waiting up to **{timeout_mins} minutes**."
        )

        start_wait = time.time()
        max_wait_seconds = timeout_mins * 60
        authenticated = False

        while time.time() - start_wait < max_wait_seconds:
            page.wait_for_timeout(3000)
            curr_url = page.url.lower()
            no_email_input = page.locator('input[type="email"]').count() == 0
            if "onboarding" not in curr_url and "login" not in curr_url and no_email_input:
                authenticated = True
                print("\n[+] Session successfully authenticated! Proceeding to automation...\n")
                send_discord_alert(webhook_url, "✅ NZXT Club Authenticated", "Authentication successful. Proceeding with quests.")
                break

        if not authenticated:
            print("[-] Login timeout reached without successful authentication. Exiting script.")
            sys.exit(1)

def run_automation():
    config = load_or_create_config()
    
    quest_categories = [
        "https://club.nzxt.com/v2/nzxt-club-quests/daily-checkin",
        "https://club.nzxt.com/v2/nzxt-club-quests/x-twitter-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/facebook-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/instagram-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/tiktok-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/reddit-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/youtube-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/twitch-quests",
        "https://club.nzxt.com/v2/nzxt-club-quests/discord-quests"
    ]
    
    with sync_playwright() as p:
        print("Launching Google Chrome...")
        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=config.get("headless_mode", False),
            viewport={"width": 1510, "height": 1232},
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--test-type"
            ]
        )
        
        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()

        # Phase 1: Authentication logic
        verify_session_authentication(page, config)

        print("\n--- Persistent Session Active: Starting Quest Processing ---")

        # Phase 2: Quest processing logic
        try:
            for cat_url in quest_categories:
                print(f"\nNavigating to category: {cat_url}")
                page.goto(cat_url)
                
                page.wait_for_timeout(3000)
                try:
                    page.wait_for_selector(".hv2-skeleton", state="detached", timeout=10000)
                except Exception:
                    pass

                is_discord = "discord-quests" in cat_url

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
                        is_claimed = link.evaluate("""el => {
                            let card = el.closest('div[style*="border"], div[class*="card"], li, div[data-block-type]') || el.parentElement;
                            if (!card) card = el;

                            const cardText = (card.innerText || '').toUpperCase();
                            if (cardText.includes('CLAIMED')) return true;

                            const hasCheckIcon = card.querySelector('.fa-check, i[class*="check"], svg[class*="check"]') !== null;
                            if (hasCheckIcon) return true;

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

                        modal = page.locator('div[role="dialog"], [class*="modal"]')
                        if modal.is_visible():
                            if is_discord:
                                print("Discord quest detected. Skipping interactive wait...")
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
