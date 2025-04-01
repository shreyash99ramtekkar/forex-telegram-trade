from service.Channel import Channel
import re
from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;
fxstreetlogger = FxTelegramTradeLogger()
from telethon import  events
from constants.Constants import TIME_FORMAT
from constants.Constants import TRADE_URL;
import math as mt
from datetime import datetime as dt
import requests
import json
logger = fxstreetlogger.get_logger(__name__)

class TradeTiten(Channel):
    
    
    TRADE_KEYWORDS = ["sl","tp (1)","tp (2)","move sl after tp1"]
    
    CLOSE_KEYWORDS = ["partial", "close","delete","cut","closing"]
    
    edit_db = {}
    
    async def connect_and_listen(self,CHANNEL_ID):
         await super().connect_and_listen(CHANNEL_ID)

      
      
    
    async def process_messages(self,event):
        message_content = event.message.message.lower()  # Convert to lowercase for case-insensitive matching
        message_id = event.message.id
        logger.info("Message content : [ "+ message_content + " ]")
        # Check if the message contains any of the keywords
        chat_title = "Private Chat"
        if hasattr(event.chat, 'title'):
            chat_title = event.chat.title
        if all(keyword in message_content for keyword in TradeTiten.TRADE_KEYWORDS):
            logger.info(f"Trade : Message passed the filters check of the channel: {chat_title}")
            trade_info = self.extract_trade_info(event.message.message,event.date)
            self.delta_order(trade_info,50)
            logger.info(f"Extracted trade info: {str(trade_info)}")
            # self.metatrader_obj.sendOrder(trade_info)
            response = requests.post(url=TRADE_URL,json=trade_info)
            if response.status_code == 200:
                # Convert string to dictionary
                response_dict = json.loads(response.text)
                # Extract order_id
                order_id = response_dict.get("order_id")
                logger.info("The request for trade summited to the MT5 api")
                logger.info("The trade info : " + str(trade_info))
                logger.info(f"Recived the response {response.text} with status code {response.status_code}" )
                if order_id:
                    TradeTiten.edit_db[message_id] = order_id
                    logger.info(f"Trade info saved in the edit_db: {str(TradeTiten.edit_db)}")
            else:
                logger.warn(f"Recived the response with status code {response.status_code}")
            # You can also add further processing here (e.g., save, forward, etc.)
        elif any(keyword in message_content for keyword in TradeTiten.CLOSE_KEYWORDS):
            logger.info(f"Close trade: Filtered message in {chat_title} : {message_content}")
            await self.close_message_update(event)
        else:
            logger.info("Message [" + message_content + "] didn't match any Keywords")
                
                
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
        sl = self.safe_float(re.search(sl_pattern, message).group(1).strip())
        tp1 = self.safe_float(re.search(tp1_pattern, message).group(1).strip())
        # setting the tp3 from tp2 since its difference is so high in trade titen
        tp3 = self.safe_float(re.search(tp2_pattern, message).group(1).strip())
        tp2 = self.safe_float((tp1+tp3)/2)
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
            "entry_price": self.safe_float(entry_price),
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "time": event_time.strftime(TIME_FORMAT),
            "channel": "tradetiten"
        }
        
        return trade_info
    
    async def close_message_update(self,event):
        if event.is_reply:
            # Get the original message
            logger.info("Reply message found. Getting original message")
            original_message = await event.get_reply_message()
            if original_message:
                original_message_id = original_message.id
                if original_message_id in TradeTiten.edit_db:
                    order_id = TradeTiten.edit_db[original_message_id]
                    logger.info(f"Order ID found in edit_db: {order_id}")
                    resopnse = requests.delete(url=TRADE_URL + "/" + str(order_id))
                    logger.info(f"Recived the response {response.text} with status code {response.status_code}" )
                    logger.info("The request for trade summited to the MT5 api")
                else:
                    logger.info("Original message ID not found in edit_db")
        else:
            logger.info('Normal message')
        # Information about the current message