from service.Channel import Channel
import re
from telethon import  events
from constants.Constants import TIME_FORMAT
from constants.Constants import TRADE_URL;

from datetime import datetime as dt
import requests

from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;
fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)

class FXStreet(Channel):
    
    CREATE_TRADE_EXP = "^([a-zA-Z]{3,6}) (sell|buy) now$" 
    
    CREATE_UPDATE_TRADE_KEYWORDS = ["stop loss","tp1","tp2"]
    
    CLOSE_KEYWORDS = ["partial", "close","delete","cut","closing"]
    
    open_order_list = []
    
    async def connect_and_listen(self,CHANNEL_ID):
        await super().connect_and_listen(CHANNEL_ID)
    
    async def process_messages(self,event):
        print(f"open_order_list = {FXStreet.open_order_list}")
        message_content = event.message.message.lower()  # Convert to lowercase for case-insensitive matching
        logger.info("Message content : [ "+ message_content + " ]")
        # Check if the message contains any of the keywords
        chat_title = "Private Chat"
        if hasattr(event.chat, 'title'):
            chat_title = event.chat.title
        # if re.fullmatch(FXStreet.CREATE_TRADE_EXP,message_content) != None:
        #     logger.info("Immediate trade without SL and TP")
        #     logger.info(f"Trade : Message passed the filters check of the channel: {chat_title}")
        #     trade_info = self.extract_trade_info(event.message.message,event.date,True)
        #     logger.info(f"Extracted trade info: {str(trade_info)}")
        #     response = requests.post(url=TRADE_URL,json=trade_info)
        #     FXStreet.open_order_list.append(trade_info)
        #     logger.info("The request for trade summited to the MT5 api")
        #     logger.info("The trade info : " + str(trade_info))
        #     logger.info(f"Recived the response {response.text} with status code {response.status_code}" )
        if all(keyword in message_content for keyword in FXStreet.CREATE_UPDATE_TRADE_KEYWORDS):
            logger.info(f"Trade : Message passed the filters check of the channel: {chat_title}")
            trade_info = self.extract_trade_info(event.message.message,event.date)
            logger.info(f"Extracted trade info: {str(trade_info)}")
            # self.metatrader_obj.sendOrder(trade_info)
            response = None
            if len(FXStreet.open_order_list) == 0:
                response = requests.post(url=TRADE_URL,json=trade_info)
            else:
                logger.info(f"PUT Request updating the stack open_order_list = {FXStreet.open_order_list}")
                response = requests.put(url=TRADE_URL,json=trade_info)
            logger.info("The request for trade summited to the MT5 api")
            logger.info("The trade info : " + str(trade_info))
            self.telegram_obj.sendMessage("The trade info : " + str(trade_info))
            logger.info(f"Recived the response {response.text} with status code {response.status_code}" )
            # You can also add further processing here (e.g., save, forward, etc.)
        # elif any(keyword in message_content for keyword in FXStreet.CLOSE_KEYWORDS):
        #     logger.info(f"Close trade: Filtered message in {chat_title} : {message_content}")
        #     await self.close_message_update(event)
        else:
            logger.info("Message [" + message_content + "] didn't match any Keywords")
                
                
    def extract_trade_info(self,message,event_time,direct_order=False):
        # Define regular expressions to capture each part
        currency_pattern = r'([A-Z]{3,6})'
        type_pattern = r'(BUY NOW|BUY LIMIT|SELL NOW|SELL LIMIT|BUY ZONE|SELL ZONE|BUY|SELL)'
        price_pattern = r'\(?(\d+\.?\d*)\s*-?\s*(\d*\.?\d*)\)?'  # Matches any number with decimal places
        sl_pattern = r'STOP LOSS\s*:\s*(\d+\.?\d*)'
        tp1_pattern = r'TP1\s*:\s*(\d+\.?\d*)'
        tp2_pattern = r'TP2\s*:\s*(\d+\.?\d*)'
        entry_price = None
        sl = None
        tp1 = None
        tp2 = None
        entry_price2 = None
        # Extract using regular expressions
        currency = re.search(currency_pattern, message).group(1).strip()
        trade_type = re.search(type_pattern, message).group(1).strip()
        if not direct_order:
            entry_price = re.search(price_pattern, message).group(1).strip()
            entry_price2 = re.search(price_pattern, message).group(2).strip()
            sl = re.search(sl_pattern, message).group(1).strip()
            tp1 = re.search(tp1_pattern, message).group(1).strip()
            tp2 = re.search(tp2_pattern, message).group(1).strip()
        if currency == "XAUUSD":
            currency = "GOLD"
            
        if trade_type == "BUY NOW":
            trade_type = "BUY"
        elif trade_type == "SELL NOW":
            trade_type = "SELL"
        elif trade_type == "SELL ZONE":
            trade_type = "SELL LIMIT"
        elif trade_type == "BUY ZONE":
            trade_type = "BUY LIMIT"
            
            
        if len(entry_price2)!=0 and entry_price2 is not None:
            if "BUY" in trade_type:
                entry_price = str(min(float(entry_price),float(entry_price2)))
            elif "SELL" in trade_type:
                entry_price = str(max(float(entry_price),float(entry_price2)))
            
            
        
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