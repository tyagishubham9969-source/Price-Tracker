import requests
import os

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set")
    exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
response = requests.get(url, timeout=10)
data = response.json()

if not data.get("ok"):
    print(f"❌ Error: {data}")
    exit(1)

messages = data.get("result", [])
if not messages:
    print("⚠️  No messages found. Please send a message to your Telegram bot first, then run this script again.")
    exit(0)

print("✅ Found chats:")
for update in messages:
    msg = update.get("message", {})
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    name = chat.get("first_name", "") + " " + chat.get("last_name", "")
    username = chat.get("username", "")
    if chat_id:
        print(f"  Chat ID : {chat_id}")
        print(f"  Name    : {name.strip()}")
        print(f"  Username: @{username}")
        print()
