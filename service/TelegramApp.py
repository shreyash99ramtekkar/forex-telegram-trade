from telethon import TelegramClient, events
import re
from datetime import datetime as dt
from constants.TelegramConstants import TELEGRAM_APP_ID
from constants.TelegramConstants import TELEGRAM_SESSION;
from constants.TelegramConstants import TELEGRAM_HASH_ID
from constants.TelegramConstants import TELEGRAM_CHANNEL_IDS
from constants.Constants import TIME_FORMAT;
from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;
from notifications.Telegram import Telegram;
import os;

telegram_obj = Telegram()
fxstreetlogger = FxTelegramTradeLogger()

logger = fxstreetlogger.get_logger(__name__)

KEYWORDS = { 
    'trade' : ["sl","tp (1)","tp (2)","move sl after tp1"],
    'close' : ["partial", "close","delete","cut","closing"]
    }

class TelegramApp:
    def __init__(self,metatrader_obj):
        # Create the client and connect
        self.client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_APP_ID, TELEGRAM_HASH_ID)
        self.metatrader_obj = metatrader_obj

    async def connect_and_listen(self):
        # Connect to the Telegram client
        logger.info("Connecting to the telegram app");
        await self.client.start()
        logger.info("Connection successful");
        # Listen for new messages with specific keywords
        @self.client.on(events.NewMessage(chats=TELEGRAM_CHANNEL_IDS))
        async def new_message_listener(event):
            message_content = event.message.message.lower()  # Convert to lowercase for case-insensitive matching
            logger.info("Message content : [ "+ message_content + " ]")
            # Check if the message contains any of the keywords
            chat_title = "Private Chat"
            if hasattr(event.chat, 'title'):
                chat_title = event.chat.title
            if all(keyword in message_content for keyword in KEYWORDS['trade']):
                logger.info(f"Trade : Filtered message in {chat_title} : {message_content}")
                trade_info = self.extract_trade_info(event.message.message,event.date)
                self.metatrader_obj.sendOrder(trade_info)
                logger.info("The trade info : " + str(trade_info))
                # You can also add further processing here (e.g., save, forward, etc.)
            elif any(keyword in message_content for keyword in KEYWORDS['close']):
                logger.info(f"Close trade: Filtered message in {chat_title} : {message_content}")
                await self.close_message_update(event)
            else:
                telegram_obj.sendMessage("Message [" + message_content + "] didn't match the Keywords" + str(KEYWORDS))

        # Keep the client running to listen for messages
        logger.info("Listening for filtered messages...")
        await self.client.run_until_disconnected()

    async def close_message_update(self,event):
        if event.is_reply:
            # Get the original message
            logger.info("Reply message found. Getting original message")
            original_message = await event.get_reply_message()
            if original_message:
                logger.info("Extracting trade info from the message")
                trade_info = self.extract_trade_info(original_message.text,original_message.date)
                self.metatrader_obj.close_trade(trade_info)
        else:
            logger.info('Normal message')
        # Information about the current message
        

    async def fetch_last_message(self):
        logger.info("Connecting to the telegram app");
        # Connect to the Telegram client
        await self.client.start()
        logger.info("Connection successful");
        # Get the most recent message from the specified channel
        messages = await self.client.get_messages(TELEGRAM_CHANNEL_IDS, limit=10)
        logger.info("Getting the messages")
        for message in messages:
            logger.info(f"Message received: {message.message}")
            if all(keyword in message.message.lower() for keyword in KEYWORDS):
                trade_info = self.extract_trade_info(message.message)
                logger.info("The trade info : " + str(trade_info))
                logger.info(f"Last message in TREND_TITEN_FX_VIP: {message.message}")
                self.metatrader_obj.sendOrder(trade_info)
                
            else:
                logger.info(f"No messages found in TREND_TITEN_FX_VIP")

    async def get_channel_id(self):
        # Connect to the Telegram client
        await self.client.start()

        # Iterate through all dialogs to list their names and IDs
        async for dialog in self.client.iter_dialogs():
            # Print the name and ID of each chat
            logger.info(f"Name: {dialog.name}, ID: {dialog.id}")

    def extract_trade_info(self,message,event_time):
        # Define regular expressions to capture each part
        currency_pattern = r'([A-Z]{3,6})'
        type_pattern = r'(BUY NOW|BUY LIMIT|SELL NOW|SELL LIMIT|BUY|SELL)'
        price_pattern = r'(\d+\.?\d*)'  # Matches any number with decimal places
        sl_pattern = r'SL\s*:\s*(\d+\.?\d*)'
        tp1_pattern = r'TP \(1\)\s*:\s*(\d+\.?\d*)'
        tp2_pattern = r'TP \(2\)\s*:\s*(\d+\.?\d*)'

        # Extract using regular expressions
        currency = re.search(currency_pattern, message).group(1).strip()
        trade_type = re.search(type_pattern, message).group(1).strip()
        entry_price = re.search(price_pattern, message).group(1).strip()
        sl = re.search(sl_pattern, message).group(1).strip()
        tp1 = re.search(tp1_pattern, message).group(1).strip()
        tp2 = re.search(tp2_pattern, message).group(1).strip()
        if currency == "XAUUSD":
            currency = "GOLD"
        # Organize into a dictionary for easy access
        trade_info = {
            "currency": currency,
            "trade_type": trade_type,
            "entry_price": entry_price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "time": event_time.strftime(TIME_FORMAT)
        }
        
        return trade_info

