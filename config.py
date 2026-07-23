"""
Configuration for the SquirrelMail monitor.
"""

# -----------------------------
# SquirrelMail
# -----------------------------

BASE_URL = "http://6n5nbusxgyw46juqo3nt5v4zuivdbc7mzm74wlhg7arggetaui4yp4id.onion"

LOGIN_PAGE = BASE_URL + "/src/login.php"
LOGIN_POST = BASE_URL + "/src/redirect.php"
INBOX_URL = BASE_URL + "/src/right_main.php?mailbox=INBOX"

USERNAME = "email"
PASSWORD = "password"

# -----------------------------
# Tor
# -----------------------------

PROXIES = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

# -----------------------------
# Telegram
# -----------------------------

BOT_TOKEN = "the_bot_token"

CHAT_ID = "ur_chat_id_here"

# -----------------------------
# Timing
# -----------------------------

CHECK_INTERVAL = 1800       # 30 minutes
TELEGRAM_POLL = 2           # seconds

# -----------------------------
# Files
# -----------------------------

COOKIE_FILE = "cookies.pkl"

LAST_MESSAGE_FILE = "last_message.txt"

CAPTCHA_FILE = "captcha.png"
