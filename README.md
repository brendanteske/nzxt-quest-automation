# NZXT Club Quest Automation

An automated script built with Python and Playwright to navigate and complete daily quests on the NZXT Club platform.

## Features

* **Automated Navigation:** Automatically loops through multiple quest categories (including X, Facebook, Instagram, TikTok, Reddit, YouTube, Twitch, and Discord) to open and complete available quests.
* **Interactive Quest Solvers:** Automates game-based quests including Worldle and NYT Wordle by executing gameplay on site and scraping revealed solutions.
* **Daily Check-In Handling:** Automatically checks in using native role locators to claim daily calendar rewards.
* **Pucci Points Giveaway Automation:** Automatically enters giveaways starting from the highest affordable entry tier, with a configurable toggle to save or spend points.
* **Automated Login & 2FA:** Fills account credentials, handles ALTCHA captcha verification, and automatically retrieves 6-digit verification codes via Gmail IMAP.
* **Auto-Dependency Setup:** Checks and installs missing Python packages (`playwright`, `beautifulsoup4`) and browser components automatically on launch.
* **Discord Webhook Alerts & Summaries:** Sends status notifications, daily run summaries, and weekly performance reports directly to Discord.
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
    "spend_pucci_points": true,
    "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
    "enable_discord_alerts": true,
    "enable_weekly_summary": true,
    "enable_daily_summary": false,
    "account_email": "YOUR_NZXT_EMAIL",
    "account_password": "YOUR_NZXT_PASSWORD",
    "gmail_app_password": "YOUR_GMAIL_APP_PASSWORD",
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
```
