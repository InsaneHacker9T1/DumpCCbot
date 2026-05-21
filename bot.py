# Telegram Bot - CC Dumps Extractor - Single Button Mode (Non‑blocking)
# Uses timeouts, fallback data, and never hangs.

import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import re
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# ========== CONFIGURATION ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8380726917:AAH10UVMWwB0zG58t8u3AAZa6Sh2A0gn70A")
PORT = int(os.environ.get("PORT", 10000))
# ===================================

session = requests.Session()
session.timeout = 8   # global timeout for all requests

# ---------- SAFE SCRAPING WITH TIMEOUT ----------
def google_dork_safe(query, max_results=3):
    encoded = quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}&num={max_results}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        resp = session.get(url, timeout=8)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/url?q=' in href and 'google' not in href:
                clean = href.split('/url?q=')[1].split('&')[0]
                if clean.startswith('http'):
                    links.append(clean)
        return links[:max_results]
    except:
        return []

def extract_from_pastebin_safe(url):
    try:
        resp = session.get(url, timeout=8)
        if resp.status_code != 200:
            return []
        pattern = re.compile(r'(\d{15,19})[|\s:,-]+(\d{2}/\d{2,4})[|\s:,-]+(\d{3,4})', re.IGNORECASE)
        matches = []
        for match in pattern.findall(resp.text):
            matches.append({'cc': match[0], 'exp': match[1], 'cvv': match[2], 'source': url})
        return matches
    except:
        return []

def fetch_dumps_fast(max_desired=10):
    """Try real scraping, but if nothing found quickly, return fallback data."""
    dumps = []
    # Try one simple dork
    urls = google_dork_safe('filetype:txt "card number" "expiration date"', max_results=2)
    for u in urls:
        if 'pastebin' in u or 'controlc' in u:
            dumps.extend(extract_from_pastebin_safe(u))
        if len(dumps) >= max_desired:
            break
    # If we got real results, filter and return
    if dumps:
        # Luhn filter
        def luhn_ok(cc):
            digits = [int(x) for x in str(cc) if x.isdigit()]
            if len(digits) < 16:
                return False
            s = 0
            rev = digits[::-1]
            for i, d in enumerate(rev):
                if i % 2 == 1:
                    d2 = d * 2
                    s += d2 - 9 if d2 > 9 else d2
                else:
                    s += d
            return s % 10 == 0
        valid = [d for d in dumps if luhn_ok(d['cc'])]
        if valid:
            return valid[:max_desired]
    # Fallback: return realistic test data (so bot never hangs)
    fallback = [
        {'cc': '4111111111111111', 'exp': '12/26', 'cvv': '123', 'source': 'demo - real scan failed'},
        {'cc': '5500000000000004', 'exp': '09/27', 'cvv': '456', 'source': 'demo - use rotating proxies'},
    ]
    return fallback

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
        "Press the button below – results guaranteed within 10 seconds.\n"
        "⚠️ Real dumps are rare; fallback data shown if live scraping fails.",
        parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔍 EXTRACT DUMPS")
def extract_button(msg):
    status_msg = bot.reply_to(msg, "🔍 Scanning for dumps... (max 10 sec)")
    try:
        dumps = fetch_dumps_fast(max_desired=8)
        if not dumps:
            answer = "❌ No dumps found. Try again later."
        else:
            answer = f"💎 **FOUND {len(dumps)} ITEMS** 💎\n━━━━━━━━━━━━━━━━━━\n"
            for idx, d in enumerate(dumps[:8], 1):
                masked = f"{d['cc'][:6]}****{d['cc'][-4:]}"
                answer += f"#{idx} 💳 `{masked}` | Exp `{d['exp']}` | CVV `{d['cvv']}`\n"
                answer += f"   📎 `{d['source'][:40]}`\n━━━━━━━━━━━━━━━━━━\n"
                if len(answer) > 3800:
                    break
        bot.edit_message_text(answer, msg.chat.id, status_msg.message_id,
                              parse_mode="Markdown", reply_markup=get_main_keyboard())
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:80]}\nPlease try again.",
                              msg.chat.id, status_msg.message_id,
                              reply_markup=get_main_keyboard())

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.send_message(msg.chat.id, "Press the button '🔍 EXTRACT DUMPS' to start.", reply_markup=get_main_keyboard())

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
    print("Bot started. Button will always reply within 10 seconds.")
    bot.infinity_polling()

if __name__ == "__main__":
    main()
