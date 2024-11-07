from telethon import TelegramClient, events
import re
from constants.TelegramConstants import TELEGRAM_APP_ID
from constants.TelegramConstants import TELEGRAM_HASH_ID
from constants.TelegramConstants import TELEGRAM_USER_NAME
from constants.TelegramConstants import CHANNEL_USERNAME
from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;

fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)

KEYWORDS = ["sl","tp (1)","tp (2)","move sl after tp1"]

class TelegramApp:
    def __init__(self,metatrader_obj):
        # Create the client and connect
        self.client = TelegramClient(TELEGRAM_USER_NAME, TELEGRAM_APP_ID, TELEGRAM_HASH_ID)
        self.metatrader_obj = metatrader_obj

    async def connect_and_listen(self):
        # Connect to the Telegram client
        logger.info("Connecting to the telegram app");
        await self.client.start()
        logger.info("Connection successful");
        # Listen for new messages with specific keywords
        @self.client.on(events.NewMessage(chats=CHANNEL_USERNAME))
        async def new_message_listener(event):
            message_content = event.message.message.lower()  # Convert to lowercase for case-insensitive matching
            logger.info(message_content)
            # Check if the message contains any of the keywords
            if all(keyword in message_content for keyword in KEYWORDS):
                logger.info(f"Filtered message in {CHANNEL_USERNAME}: {event.message.message}")
                trade_info = self.extract_trade_info(message_content)
                self.metatrader_obj.sendOrder(trade_info)
                logger.info("The trade info : " + str(trade_info))
                # You can also add further processing here (e.g., save, forward, etc.)

        # Keep the client running to listen for messages
        logger.info("Listening for filtered messages...")
        await self.client.run_until_disconnected()

    async def fetch_last_message(self):
        logger.info("Connecting to the telegram app");
        # Connect to the Telegram client
        await self.client.start()
        logger.info("Connection successful");
        # Get the most recent message from the specified channel
        messages = await self.client.get_messages(CHANNEL_USERNAME, limit=10)
        logger.info("Getting the messages")
        for message in messages:
            if all(keyword in message.message.lower() for keyword in KEYWORDS):
                trade_info = self.extract_trade_info(message.message)
                logger.info("The trade info : " + str(trade_info))
                logger.info(f"Last message in {CHANNEL_USERNAME}: {message.message}")
                self.metatrader_obj.sendOrder(trade_info)
                
            else:
                logger.info(f"No messages found in {CHANNEL_USERNAME}")


    def extract_trade_info(self,message):
        # Define regular expressions to capture each part
        currency_pattern = r'([A-Z]{3,6})'
        type_pattern = r'(BUY NOW|BUY LIMIT|SELL NOW|SELL LIMIT)'
        price_pattern = r'(\d+\.\d+)'  # Matches any number with decimal places
        sl_pattern = r'SL\s*:\s*(\d+\.\d+)'
        tp1_pattern = r'TP \(1\)\s*:\s*(\d+\.\d+)'
        tp2_pattern = r'TP \(2\)\s*:\s*(\d+\.\d+)'

        # Extract using regular expressions
        currency = re.search(currency_pattern, message).group(1)
        trade_type = re.search(type_pattern, message).group(1)
        entry_price = re.search(price_pattern, message).group(1)
        sl = re.search(sl_pattern, message).group(1)
        tp1 = re.search(tp1_pattern, message).group(1)
        tp2 = re.search(tp2_pattern, message).group(1)

        # Organize into a dictionary for easy access
        trade_info = {
            "currency": currency,
            "trade_type": trade_type,
            "entry_price": entry_price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2
        }
        
        return trade_info

