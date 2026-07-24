Markdown
# NZXT Club Quest Automation

An automated script built with Python and Playwright to navigate and complete daily quests on the NZXT Club platform.

## Features

* **Automated Navigation:** Automatically logs in and loops through multiple quest categories (including X, Facebook, Instagram, TikTok, Reddit, YouTube, Twitch, and Discord).
* **Daily Check-In Handling:** Automatically checks and claims daily calendar rewards.
* **Interactive Discord Puzzles:** Automatically detects Discord puzzle quests and pauses with a dual 2-minute timeout or manual terminal confirmation so you can solve text inputs.
* **Persistent Session:** Uses a local persistent browser profile so you only need to log in manually during the first run.

## Prerequisites

* Python 3.8 or higher
* Google Chrome installed on your system

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/brendanteske/nzxt-quest-automation.git](https://github.com/brendanteske/nzxt-quest-automation.git)
   cd nzxt-quest-automation
Install the required dependencies:

Bash
pip install playwright
playwright install chromium
Usage
Run the script:

Python
python automate_quests.py
The script will launch a Google Chrome browser instance and navigate to NZXT Club. Log into your account manually in the browser window, then return to your terminal and press ENTER to start the automation.

For Discord text-entry puzzle quests, type your answer in ALL CAPS directly in the browser and press ENTER in the terminal once done (or wait up to 2 minutes for it to automatically proceed).
