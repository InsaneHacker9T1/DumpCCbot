# Telegram Bot - CC Dumps Extractor - Single Button Mode
# For darkweb support, run on VPS with Tor and set TOR_ENABLED=true

import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import re
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# ========== CONFIGURATION ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8380726917:AAH10UVMWwB0zG58t8u3AAZa6Sh2A0gn70A")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7409867517"))
TOR_ENABLED = os.environ.get("TOR_ENABLED", "false").lower() == "true"
PORT = int(os.environ.get("PORT", 10000))
# ===================================

session = requests.Session()

# ---------- Dorking functions ----------
def google_dork(query, max_results=5):
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

def fetch_all_dumps(max_results=20):
    dork_queries = [
        'filetype:txt "card number" "expiration date"',
        'intitle:"credit card" "expiry" "cvv" -forum -blog',
        'inurl:dump "cc" "cvv" filetype:txt',
        '"Track1" "Track2" .txt',
        'filetype:csv "credit card number"'
    ]
    all_dumps = []
    for dork in dork_queries:
        urls = google_dork(dork, max_results=2)
        for url in urls:
            if isinstance(url, str) and ('pastebin' in url or 'controlc' in url):
                dumps = extract_from_pastebin(url)
                all_dumps.extend(dumps)
            if len(all_dumps) >= max_results:
                break
        time.sleep(random.uniform(1, 2))
        if len(all_dumps) >= max_results:
            break
    # Also try forum links
    forum_dorks = ['site:cracked.to "cc dump"', 'site:nulled.to "track1"']
    for fd in forum_dorks:
        urls = google_dork(fd, max_results=2)
        for url in urls:
            if isinstance(url, str):
                dumps = extract_from_pastebin(url)
                all_dumps.extend(dumps)
    return all_dumps[:max_results]

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

def format_output(dumps):
    if not dumps:
        return "❌ No valid dumps found.\nTry again later or use a different source."
    result = f"💎 **FOUND {len(dumps)} HIGH-QUALITY DUMPS** 💎\n━━━━━━━━━━━━━━━━━━\n"
    for idx, d in enumerate(dumps[:15], 1):
        masked = f"{d['cc'][:6]}****{d['cc'][-4:]}"
        result += f"#{idx} 💳 `{masked}` | Exp `{d['exp']}` | CVV `{d.get('cvv', '???')}`\n"
        result += f"   📎 `{d['source'][:50]}`\n━━━━━━━━━━━━━━━━━━\n"
        if len(result) > 3800:
            break
    return result

# ---------- Keyboard ----------
def get_main_keyboard():
    kb = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=False)
    kb.add(KeyboardButton("🔍 EXTRACT DUMPS"))
    return kb

# ---------- Bot ----------
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(msg):
    bot.send_message(msg.chat.id, 
        "✨ **CC DUMP EXTRACTOR** ✨\n\n"
        "Press the button below to search for credit card dumps from Google dorks and pastebin.\n"
        "⚠️ Results are filtered by Luhn algorithm.\n"
        "⏳ Each scan takes 30-90 seconds.",
        parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔍 EXTRACT DUMPS")
def extract_button(msg):
    # Send initial message
    status_msg = bot.reply_to(msg, "🔍 Scanning internet for dumps...\n⏳ This may take 1-2 minutes.")
    try:
        all_dumps = fetch_all_dumps(max_results=20)
        good = high_quality_filter(all_dumps)
        answer = format_output(good)
        bot.edit_message_text(answer, msg.chat.id, status_msg.message_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:100]}\nTry again.", msg.chat.id, status_msg.message_id, reply_markup=get_main_keyboard())

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.send_message(msg.chat.id, "Press the button '🔍 EXTRACT DUMPS' to start searching.", reply_markup=get_main_keyboard())

# Fallback for any other text
@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.send_message(msg.chat.id, "Please use the button below.", reply_markup=get_main_keyboard())

# ---------- HTTP server for Render ----------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, format, *args):
        pass

def run_http():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    server.serve_forever()

def main():
    threading.Thread(target=run_http, daemon=True).start()
    print("Bot started. Press button to extract dumps.")
    bot.infinity_polling()

if __name__ == "__main__":
    main()
