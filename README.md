# NZXT Club Quest Automation

An automated script built with Python and Playwright to navigate and complete daily quests on the NZXT Club platform.

## Features

* **Automated Navigation:** Automatically loops through multiple quest categories (including X, Facebook, Instagram, TikTok, Reddit, YouTube, Twitch, and Discord) to open and complete available quests.
* **Interactive Quest Solvers:** Automates game-based quests including Worldle and NYT Wordle by executing gameplay on site and scraping revealed solutions.
* **AI Fallback Solver:** Integrates `google-genai` (Gemini API) to dynamically analyze and solve modal quest prompts if automated scraping fails.
* **Daily Check-In Handling:** Automatically checks in using native role locators to claim daily calendar rewards.
* **Automated Login & 2FA:** Fills account credentials, handles ALTCHA captcha verification, and automatically retrieves 6-digit verification codes via Gmail IMAP.
* **Auto-Dependency Setup:** Checks and installs missing Python packages (`playwright`, `beautifulsoup4`, `google-genai`) and browser components automatically on launch.
* **Discord Webhook Alerts:** Sends status notifications to Discord if manual intervention or login verification is needed.
* **Timestamped Weekly Logging:** Appends ISO-formatted timestamps to console outputs and writes to a local log file that resets automatically every 7 days.
* **Persistent Session:** Saves session details in a local browser profile to bypass repeat logins on subsequent runs.

## Prerequisites

* Python 3.8 or higher
* Google Chrome installed on your system

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/brendanteske/nzxt-quest-automation.git](https://github.com/brendanteske/nzxt-quest-automation.git)
   cd nzxt-quest-automation
   ```

2. Run the script (dependencies will be verified and installed automatically):
   ```bash
   python automate_quests.py
   ```

## Configuration

On the first run, the script automatically generates a `config.json` file in the project directory. Populate this file with your details:

```json
{
    "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
    "account_email": "YOUR_NZXT_EMAIL",
    "account_password": "YOUR_NZXT_PASSWORD",
    "gmail_app_password": "YOUR_GMAIL_APP_PASSWORD",
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
    "email_sender_filter": "do-not-reply@club.nzxt.com",
    "headless_mode": false,
    "login_timeout_minutes": 5,
    "dependencies_installed": false
}
```

## Usage

1. Launch the automation:
   ```bash
   python automate_quests.py
   ```

2. The script checks for active authentication. If unauthenticated, it automatically completes the login sequence, solves the captcha, and processes 2FA verification.

3. If manual intervention is required, the script sends an alert to your Discord webhook and waits up to the configured timeout for you to complete login manually before proceeding with quest processing.
