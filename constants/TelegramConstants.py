import os
from dotenv import load_dotenv

# load .env file to environment
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_SESSION = os.getenv("PROFILE")


TELEGRAM_APP_ID = os.getenv("APP_ID")
TELEGRAM_HASH_ID = os.getenv("HASH_ID")
TELEGRAM_PHONE = os.getenv("PHONE")

TRADE_TITEN_TELE_IDS = [ int(item) for item in os.getenv("TRADE_TITEN_TELE_IDS","-1002049641249,-1002455402609").split(',') ]
FX_STREET_TELE_IDS = [ int(item) for item in os.getenv("FX_STREET_TELE_IDS","-1002479981246").split(',') ]