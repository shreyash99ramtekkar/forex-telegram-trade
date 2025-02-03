from service.Channel import Channel
import re
from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;
fxstreetlogger = FxTelegramTradeLogger()
from telethon import  events
from constants.Constants import TIME_FORMAT
from constants.Constants import TRADE_URL;
from constants.TelegramConstants import TRADE_TITEN_TELE_IDS
from datetime import datetime as dt
import requests
logger = fxstreetlogger.get_logger(__name__)

class TradeTiten(Channel):
    
    
    TRADE_KEYWORDS = ["sl","tp (1)","tp (2)","move sl after tp1"]
    
    CLOSE_KEYWORDS = ["partial", "close","delete","cut","closing"]
    
    
    async def connect_and_listen(self):
        # Connect to the Telegram client
        logger.info("Connecting to the telegram app");
        await Channel.client.start()
        logger.info("Connection successful");
        # Listen for new messages with specific keywords
        @Channel.client.on(events.NewMessage(chats=TRADE_TITEN_TELE_IDS))
        async def new_message_listener(event):
            await self.process_messages(event)  
        # Keep the client running to listen for messages
        logger.info("Listening for filtered messages...")
        await Channel.client.run_until_disconnected()
    
    async def process_messages(self,event):
        message_content = event.message.message.lower()  # Convert to lowercase for case-insensitive matching
        logger.info("Message content : [ "+ message_content + " ]")
        # Check if the message contains any of the keywords
        chat_title = "Private Chat"
        if hasattr(event.chat, 'title'):
            chat_title = event.chat.title
        if all(keyword in message_content for keyword in TradeTiten.TRADE_KEYWORDS):
            logger.info(f"Trade : Message passed the filters check of the channel: {chat_title}")
            trade_info = self.extract_trade_info(event.message.message,event.date)
            logger.info(f"Extracted trade info: {str(trade_info)}")
            # self.metatrader_obj.sendOrder(trade_info)
            response = requests.post(url=TRADE_URL,json=trade_info)
            logger.info("The request for trade summited to the MT5 api")
            logger.info("The trade info : " + str(trade_info))
            logger.info(f"Recived the response {response.text} with status code {response.status_code}" )
            # You can also add further processing here (e.g., save, forward, etc.)
        elif any(keyword in message_content for keyword in TradeTiten.CLOSE_KEYWORDS):
            logger.info(f"Close trade: Filtered message in {chat_title} : {message_content}")
            await self.close_message_update(event)
        else:
            TradeTiten.telegram_obj.sendMessage("Message [" + message_content + "] didn't match any Keywords")
                
                
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
        if trade_type == "BUY NOW":
            trade_type = "BUY"
        elif trade_type == "SELL NOW":
            trade_type = "SELL"
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
    
    async def close_message_update(self,event):
        if event.is_reply:
            # Get the original message
            logger.info("Reply message found. Getting original message")
            original_message = await event.get_reply_message()
            if original_message:
                logger.info("Extracting trade info from the message")
                trade_info = self.extract_trade_info(original_message.text,original_message.date)
                logger.info(f"Extracted trade info: {str(trade_info)}")
                # self.metatrader_obj.sendOrder(trade_info)
                response = requests.delete(url=TRADE_URL,json=trade_info)
                logger.info("The request for trade summited to the MT5 api")
                logger.info("The trade info : " + str(trade_info))
                logger.info(f"Recived the response {response.text} with status code {response.status_code}" )
        else:
            logger.info('Normal message')
        # Information about the current message