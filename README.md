# Price Tracker

Tracks Sonos Era 300 prices on Amazon and Flipkart.
Sends Telegram deal alerts when price drops below threshold.

## Requirements

    pip install requests beautifulsoup4

## Run

    python3 main.py

## Environment Variables
- TELEGRAM_BOT_TOKEN - from @BotFather on Telegram
- TELEGRAM_CHAT_ID - your chat ID (run get_chat_id.py to find it)
