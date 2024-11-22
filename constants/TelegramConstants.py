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

TELEGRAM_CHANNEL_IDS = [ int(item) for item in os.getenv("TELEGRAM_IDS").split(',') ]
