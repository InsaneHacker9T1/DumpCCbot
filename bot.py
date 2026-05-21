# Telegram Bot - CC Dumps Extractor with Persistent Keyboard + Attractive Formatting
# Install: pip install python-telegram-bot requests[socks] stem beautifulsoup4
# Run with Tor service active (sudo systemctl start tor)

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import json
import re
import time
import random
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
from urllib.parse import quote_plus

# ========== CONFIGURATION ==========
BOT_TOKEN = "8380726917:AAH10UVMWwB0zG58t8u3AAZa6Sh2A0gn70A"
TOR_SOCKS5 = "socks5://127.0.0.1:9050"
# Active carding markets (Tor required) - Updated May 2026
ONION_SITES = [
    "http://briansclubcmrcck.onion",
    "http://russianmarket.su",
    "http://styxshop.onion",
    "http://torzonmarket.onion",
    "http://wtnorth.onion",
    "http://blackstash.onion",
]
# ===================================

session = requests.Session()
session.proxies = {'http': TOR_SOCKS5, 'https': TOR_SOCKS5}

def renew_tor_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password="")
        controller.signal(Signal.NEWNYM)
        time.sleep(2)

def google_dork(query, max_results=10):
    encoded = quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded}&num={max_results}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/url?q=' in href and 'google' not in href:
                clean = href.split('/url?q=')[1].split('&')[0]
                links.append(clean)
        return links[:max_results]
    except:
        return []

def extract_from_pastebin(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        content = resp.text
        pattern = re.compile(r'(\d{15,19})[|\s:,-]+(\d{2}/\d{2,4})[|\s:,-]+(\d{3,4})', re.IGNORECASE)
        matches = []
        for match in pattern.findall(content):
            matches.append({
                'cc': match[0],
                'exp': match[1],
                'cvv': match[2],
                'source': url
            })
        return matches
    except:
        return []

def scan_onion_market(url, limit=10):
    try:
        resp = session.get(url, timeout=20)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        dumps = []
        patterns = [
            r'(\d{15,16})\|(\d{2}/\d{2,4})\|(\d{3,4})',
            r'(\d{15,16})\s+(\d{2}/\d{2,4})\s+(\d{3,4})',
            r'cc[:\s]*(\d{15,16}).*?exp[:\s]*(\d{2}/\d{2,4}).*?cvv[:\s]*(\d{3,4})',
            r'track1[:\s]*%?([B0-9]{15,19})\^.*?\^(\d{2}/\d{2,4})'
        ]
        for pattern in patterns:
            for match in re.findall(pattern, resp.text, re.IGNORECASE | re.DOTALL):
                if len(match) >= 2:
                    dumps.append({
                        'cc': match[0],
                        'exp': match[1] if len(match) > 1 else 'N/A',
                        'cvv': match[2] if len(match) > 2 else 'N/A',
                        'track2': f";{match[0]}={match[1]}?",
                        'source': url
                    })
        return dumps[:limit]
    except:
        return []

def fetch_from_dorking(count):
    dork_queries = [
        'filetype:txt "card number" "expiration date"',
        'intitle:"credit card" "expiry" "cvv" -forum -blog',
        'inurl:dump "cc" "cvv" filetype:txt',
        '"BIN" "CC" "dump" filetype:log',
        'index of / "cc_dump"',
        'intitle:"dump" intext:"credit card"',
        '"Track1" "Track2" .txt',
        'filetype:csv "credit card number"',
        '"cardholder name" "card number" filetype:xls',
        'inurl:carding intext:"cc" -pastebin'
    ]
    all_dumps = []
    for dork in dork_queries[:count]:
        results = google_dork(dork, max_results=3)
        for url in results:
            if url and isinstance(url, str):
                dumps = extract_from_pastebin(url)
                all_dumps.extend(dumps)
        time.sleep(random.uniform(1, 3))
        if len(all_dumps) >= count:
            break
    return all_dumps[:count]

def fetch_from_forum_search():
    forum_dorks = [
        'site:cracked.to "cc dump"',
        'site:nulled.to "track1" "track2"',
        'site:leakforums.net "cvv"'
    ]
    results = []
    for dork in forum_dorks:
        urls = google_dork(dork, max_results=5)
        for url in urls:
            if url and isinstance(url, str):
                results.append(url)
    return results

def luhn_check(num):
    digits = [int(x) for x in str(num) if x.isdigit()]
    if len(digits) < 16:
        return False
    checksum = 0
    reverse = digits[::-1]
    for i, d in enumerate(reverse):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0

def high_quality_filter(dumps):
    return [d for d in dumps if luhn_check(d.get('cc', ''))]

def format_dump_output(dumps, source_name):
    if not dumps:
        return "❌ **No valid dumps found.**\nTry another source or increase count."
    result = f"💎 **{source_name}** 💎\n`Found: {len(dumps)} high-quality dumps`\n━━━━━━━━━━━━━━━━━━\n"
    for idx, d in enumerate(dumps[:20], 1):
        cc_masked = f"{d['cc'][:6]}****{d['cc'][-4:]}"
        result += f"┌ **#{idx}**\n│ 💳 `{cc_masked}`\n│ 📅 Exp: `{d['exp']}`\n│ 🔐 CVV: `{d.get('cvv', 'N/A')}`\n"
        if 'track2' in d:
            result += f"│ 📀 Track2: `{d['track2'][:30]}...`\n"
        result += f"└ 🌐 `{d['source'][:40]}`\n━━━━━━━━━━━━━━━━━━\n"
        if len(result) > 3800:
            break
    return result

def get_persistent_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    buttons = [
        KeyboardButton("🔍 /dork"), KeyboardButton("🌑 /darkweb"),
        KeyboardButton("📄 /pastebin"), KeyboardButton("💬 /forums"),
        KeyboardButton("🎯 /all"), KeyboardButton("ℹ️ /help")
    ]
    keyboard.add(*buttons)
    return keyboard

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(msg):
    welcome = (
        "✨ **CC DUMP EXTRACTOR v2.0** ✨\n"
        "┌─────────────────────┐\n"
        "│  ✅ Persistent menu below\n"
        "│  🌐 Uses: Tor + Dorks\n"
        "│  ⚡ High-quality filter (Luhn)\n"
        "└─────────────────────┘\n\n"
        "⚙️ *Tap any button to extract dumps*"
    )
    bot.send_message(msg.chat.id, welcome, parse_mode="Markdown", reply_markup=get_persistent_keyboard())

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    help_txt = (
        "📖 **Command Guide**\n"
        "━━━━━━━━━━━━━━━━━\n"
        "🔍 `/dork <count>` – Google dorks for exposed dumps\n"
        "🌑 `/darkweb <count>` – Scrape .onion markets (Tor required)\n"
        "📄 `/pastebin <count>` – Search pastebin-style sites\n"
        "💬 `/forums <count>` – Fetch carding forum links\n"
        "🎯 `/all <count>` – Combine all sources\n"
        "ℹ️ `/help` – This menu\n\n"
        "💡 *Example:* `/dork 15`"
    )
    bot.send_message(msg.chat.id, help_txt, parse_mode="Markdown", reply_markup=get_persistent_keyboard())

@bot.message_handler(commands=['dork'])
def dork_cmd(msg):
    try:
        parts = msg.text.split()
        count = int(parts[1]) if len(parts) > 1 else 10
        count = min(count, 50)
    except:
        count = 10
    status = bot.reply_to(msg, "⚙️ `Running Google dorks...`\n⏳ *This may take 30-60 sec*", parse_mode="Markdown")
    dumps = fetch_from_dorking(count)
    filtered = high_quality_filter(dumps)
    result = format_dump_output(filtered, "GOOGLE DORK DUMPS")
    bot.edit_message_text(result, msg.chat.id, status.message_id, parse_mode="Markdown", reply_markup=get_persistent_keyboard())

@bot.message_handler(commands=['darkweb'])
def darkweb_cmd(msg):
    try:
        parts = msg.text.split()
        count = int(parts[1]) if len(parts) > 1 else 10
        count = min(count, 30)
    except:
        count = 10
    status = bot.reply_to(msg, "🌑 `Accessing darkweb markets via Tor...`\n⏳ *Please wait*", parse_mode="Markdown")
    all_dumps = []
    for site in ONION_SITES:
        dumps = scan_onion_market(site, limit=count // len(ONION_SITES) + 1)
        all_dumps.extend(dumps)
        if len(all_dumps) >= count:
            break
    filtered = high_quality_filter(all_dumps)
    result = format_dump_output(filtered, "DARKWEB MARKET DUMPS")
    bot.edit_message_text(result, msg.chat.id, status.message_id, parse_mode="Markdown", reply_markup=get_persistent_keyboard())

@bot.message_handler(commands=['pastebin'])
def pastebin_cmd(msg):
    try:
        parts = msg.text.split()
        count = int(parts[1]) if len(parts) > 1 else 5
    except:
        count = 5
    status = bot.reply_to(msg, "📄 `Searching pastebin...`", parse_mode="Markdown")
    search_terms = ['cc dump', 'cvv site:pastebin.com', 'track1 track2']
    dumps = []
    for term in search_terms[:count]:
        urls = google_dork(term, max_results=5)
        for url in urls:
            if 'pastebin.com' in url or 'controlc' in url:
                extracted = extract_from_pastebin(url)
                dumps.extend(extracted)
    filtered = high_quality_filter(dumps)
    result = format_dump_output(filtered, "PASTEBIN DUMPS")
    bot.edit_message_text(result, msg.chat.id, status.message_id, parse_mode="Markdown", reply_markup=get_persistent_keyboard())

@bot.message_handler(commands=['forums'])
def forums_cmd(msg):
    status = bot.reply_to(msg, "💬 `Scanning carding forums...`", parse_mode="Markdown")
    forums = fetch_from_forum_search()
    if not forums:
        result = "❌ No forum links found.\nTry `/dork` for alternative method."
    else:
        result = "🔗 **CARDING FORUM LINKS** (visit via Tor)\n━━━━━━━━━━━━━━━━━━\n"
        for url in forums[:10]:
            result += f"• `{url}`\n"
    bot.edit_message_text(result, msg.chat.id, status.message_id, parse_mode="Markdown", reply_markup=get_persistent_keyboard())

@bot.message_handler(commands=['all'])
def all_sources_cmd(msg):
    try:
        parts = msg.text.split()
        total = int(parts[1]) if len(parts) > 1 else 15
    except:
        total = 15
    status = bot.reply_to(msg, "🔄 `Running ALL extraction methods...`\n⏳ *ETA: 2-3 minutes*", parse_mode="Markdown")
    dumps = []
    dumps.extend(fetch_from_dorking(total // 3))
    for site in ONION_SITES[:3]:
        dumps.extend(scan_onion_market(site, limit=total // 6))
    dumps = high_quality_filter(dumps)[:total]
    result = format_dump_output(dumps, "COMBINED SOURCES")
    bot.edit_message_text(result, msg.chat.id, status.message_id, parse_mode="Markdown", reply_markup=get_persistent_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    # If user types something not a command, show keyboard hint
    bot.send_message(msg.chat.id, "⚠️ Please use the buttons below or type /help", reply_markup=get_persistent_keyboard())

def main():
    print("🔥 CC DUMP EXTRACTOR v2.0 ACTIVE 🔥")
    print("Persistent keyboard enabled. Tor required.")
    bot.infinity_polling()

if __name__ == "__main__":
    main()