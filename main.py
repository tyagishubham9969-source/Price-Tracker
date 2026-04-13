import requests
from bs4 import BeautifulSoup
import datetime
import os

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Must contain at least ONE of these to be considered Sonos
REQUIRED_KEYWORDS = ["sonos"]

# If any of these are found, it's NOT the speaker
EXCLUDE_KEYWORDS = [
    "wall mount", "mount", "stand", "bracket", "holder",
    "cable", "cover", "case", "adapter", "remote", "pegzone",
    "accessory", "bundle", "pack", "combo", "pair"
]

# Real Sonos Era 300 price range (in ₹)
MIN_PRICE = 15000
MAX_PRICE = 100000


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram not configured — skipping notification")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ Telegram notification sent!")
        else:
            print(f"⚠️  Telegram error: {resp.text}")
    except Exception as e:
        print(f"⚠️  Telegram exception: {e}")


def is_real_speaker(title, price, link=""):
    title_lower = title.lower()
    link_lower = link.lower()

    # Must contain "sonos"
    if not any(kw in title_lower for kw in REQUIRED_KEYWORDS):
        return False

    # Must not contain accessory keywords
    if any(kw in title_lower for kw in EXCLUDE_KEYWORDS):
        return False

    # Must be in a realistic price range for this speaker
    if price < MIN_PRICE or price > MAX_PRICE:
        return False

    # If we have a link, it must point to the Era 300 specifically
    if link and link != "N/A" and "era-300" not in link_lower:
        return False

    return True


def scrape_amazon():
    url = "https://www.amazon.in/s?k=sonos+era+300+speaker"
    results = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", {"data-component-type": "s-search-result"})
        for item in items[:15]:
            try:
                title = item.h2.text.strip()
                price_tag = item.find("span", {"class": "a-price-whole"})
                if not price_tag:
                    continue
                price_num = int(price_tag.text.replace(",", "").replace(".", "").strip())

                link_tag = item.find("a", {"class": lambda c: c and "a-link-normal" in c}, href=True)
                if not link_tag:
                    link_tag = item.find("a", href=lambda h: h and "/dp/" in h)
                link = "https://www.amazon.in" + link_tag["href"].split("?")[0] if link_tag else "N/A"

                if not is_real_speaker(title, price_num, link):
                    continue

                results.append(("Amazon", title, price_num, link))
            except Exception:
                continue
    except Exception as e:
        print(f"❌ Amazon scrape failed: {e}")
    return results


def scrape_flipkart():
    url = "https://www.flipkart.com/search?q=sonos+era+300+speaker"
    results = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("div", {"class": "_1AtVbE"})
        for item in items[:15]:
            try:
                title_tag = (
                    item.find("a", {"class": "s1Q9rs"}) or
                    item.find("div", {"class": "_4rR01T"}) or
                    item.find("a", {"class": "IRpwTa"})
                )
                price_tag = item.find("div", {"class": "_30jeq3"})
                if not title_tag or not price_tag:
                    continue
                title = title_tag.text.strip()
                price_str = price_tag.text.replace("₹", "").replace(",", "").strip()
                price_num = int(price_str)

                link_tag = title_tag if title_tag.name == "a" else item.find("a", href=True)
                link = "https://www.flipkart.com" + link_tag["href"] if link_tag and link_tag.get("href") else "N/A"

                if not is_real_speaker(title, price_num, link):
                    continue

                results.append(("Flipkart", title, price_num, link))
            except Exception:
                continue
    except Exception as e:
        print(f"❌ Flipkart scrape failed: {e}")
    return results


def run_check():
    print("TOKEN:", TELEGRAM_BOT_TOKEN)
    print("CHAT:", TELEGRAM_CHAT_ID)
    print(f"\n📊 SONOS ERA 300 DEAL REPORT — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_results = scrape_amazon() + scrape_flipkart()

    if not all_results:
        print("❌ No Sonos Era 300 speaker listings found (may have been blocked or out of stock)")
        send_telegram(
            f"❌ *Sonos Era 300 — No listings found*\n"
            f"_Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_\n"
            f"Amazon/Flipkart may have blocked the request. Will retry next run."
        )
        return

    print(f"\n{'Platform':<12} {'Price':>10}   Title")
    print("-" * 60)
    for platform, title, price, link in all_results:
        short_title = title[:55] + "..." if len(title) > 55 else title
        print(f"{platform:<12} ₹{price:>9,}   {short_title}")
        print(f"             🔗 {link}\n")

    best = min(all_results, key=lambda x: x[2])
    platform, title, price, link = best

    print(f"\n🔥 BEST DEAL FOUND")
    print(f"Platform : {platform}")
    print(f"Product  : {title}")
    print(f"Price    : ₹{price:,}")
    print(f"Link     : {link}")

    CRAZY_DEAL_THRESHOLD = 40000

    if price <= CRAZY_DEAL_THRESHOLD:
        print("🔥🔥 CRAZY DEAL — BUY NOW!")
        message = (
            f"🔥🔥 *CRAZY DEAL — Sonos Era 300*\n\n"
            f"*Platform:* {platform}\n"
            f"*Product:* {title}\n"
            f"*Price:* ₹{price:,}\n"
            f"*Link:* [Buy Now]({link})\n\n"
            f"_Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} — BUY NOW!_"
        )
    else:
        print(f"⏳ Price ₹{price:,} is above ₹{CRAZY_DEAL_THRESHOLD:,} — wait for drop")
        message = (
            f"📊 *Sonos Era 300 — Daily Report*\n\n"
            f"*Platform:* {platform}\n"
            f"*Best Price Today:* ₹{price:,}\n"
            f"*Link:* [View Product]({link})\n\n"
            f"⏳ _Above ₹{CRAZY_DEAL_THRESHOLD:,} threshold. Waiting for a drop..._\n"
            f"_Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_"
        )
    send_telegram(message)


run_check()
