# AlphaBot - Python Telegram Bot

This Telegram Bot is structured using the robust `pyTelegramBotAPI` synchronous toolkit.

## 📁 Included Files
- `bot.py`: Full python code with automated welcome handler, help menus, database actions, and echo services.
- `.env`: Configurations template comprising your Telegram credentials securely.
- `requirements.txt`: Package dependencies manager listing appropriate pyTelegramBotAPI installs.

## 🛠️ Step-by-Step Installation instructions

### Step 1: Install Python
Ensure Python 3.9+ is installed on your computer. Download from [python.org](https://www.python.org/downloads/). Open your command line or Terminal to verify:
```bash
python --version
```

### Step 2: Extract and Setup Folder
Put all generated files (`bot.py`, `requirements.txt`, `.env`) inside a clean folder on your computer.

### Step 3: Install Dependencies
Open your Terminal inside that directory and execute:
```bash
pip install -r requirements.txt
```

### Step 4: Verify credentials in .env
Open the `.env` file in any text editor. Ensure your bot token and admin ID are represented:
```env
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_ID=YOUR_ADMIN_ID_HERE
```

### Step 5: Start the Bot Polling Hook
Launch your bot via terminal:
```bash
python bot.py
```
Go to Telegram, search for your bot, and send **/start** to test it out!

---

## ⚡ Hosting 24/7 (Deploying to Cloud Servers)

If you turn off your laptop, the bot will stop working. To run it 24/7 for FREE, follow these easy steps:

### Option A: Render.com (Highly Recommended)
1. Push your folder to a private **GitHub Repository**.
2. Sign up on [Render.com](https://render.com) and create a new **Background Worker**.
3. Choose your GitHub repository.
4. Set the following properties:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Go to **Environment Settings** on Render, and add raw variables manually:
   - `BOT_TOKEN` = `YOUR_BOT_TOKEN_HERE`
   - `ADMIN_ID` = `YOUR_ADMIN_ID_HERE`
6. Click deploy! Your bot is now running 24/7 on the cloud!

### Option B: Railway.app / Heroku
Similar setup. Connect GitHub, provision a worker block, input configuration variables, and run `python bot.py`.
