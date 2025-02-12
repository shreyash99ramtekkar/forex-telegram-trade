from service.Channel import Channel
import re
from telethon import  events
from constants.Constants import TIME_FORMAT
from constants.Constants import TRADE_URL;
import json
from datetime import datetime as dt
import requests

from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;
fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)

class FXStreet(Channel):
    
    CREATE_TRADE_EXP = "^([a-zA-Z]{3,6}) (sell|buy) now$" 
    
    CREATE_UPDATE_TRADE_KEYWORDS = ["STOP LOSS","TP1","TP2"]
    
    CLOSE_KEYWORDS = ["partial", "close","delete","cut","closing"]
    
    message_store = {
                    "GOLD BUY": [],
                    "GOLD SELL": []
                    }    
    async def connect_and_listen(self,CHANNEL_ID):
        
        @self.client.on(events.NewMessage(chats=CHANNEL_ID))
        async def new_message_listener(event):
            await self.process_messages(event)  
            
        @self.client.on(events.MessageEdited(chats=CHANNEL_ID))
        async def edited_message_listener(event):
            await self.process_messages(event)
            
        await self.client.run_until_disconnected()
                
    
    
    async def process_messages(self,event):
        message_content = event.message.text
        message_id = event.message.id # Convert to lowercase for case-insensitive matching
        logger.info(f"message store = {FXStreet.message_store}")
        logger.info("Message content : [ "+ message_content + " ]")
        # Check if the message contains any of the keywords
        chat_title = "Private Chat"
        if hasattr(event.chat, 'title'):
            chat_title = event.chat.title
        if re.fullmatch(FXStreet.CREATE_TRADE_EXP,message_content,re.IGNORECASE) != None:
            logger.info("Immediate trade without SL and TP")
            logger.info(f"Trade : Message passed the filters check of the channel: {chat_title}")
            trade_info = self.extract_trade_info(event.message.message,event.date,True)
            logger.info(f"Extracted trade info: {str(trade_info)}")
            response = requests.post(url=TRADE_URL,json=trade_info)
            # Convert string to dictionary
            response_dict = json.loads(response.text)
            # Extract order_id
            order_id = response_dict.get("order_id")
            logger.info("The request for trade summited to the MT5 api")
            logger.info("The trade info : " + str(trade_info))
            logger.info(f"Recived the response {response.text} with status code {response.status_code}" )
            if order_id is not None:
                FXStreet.message_store[self.generate_key(trade_info)].append(order_id)
            logger.info(f"Message store={str(FXStreet.message_store)}")
        elif all(keyword in message_content.upper() for keyword in FXStreet.CREATE_UPDATE_TRADE_KEYWORDS):
            logger.info(f"Trade : Message passed the filters check of the channel: {chat_title}")
            trade_info = self.extract_trade_info(event.message.message,event.date)
            logger.info(f"Extracted trade info: {str(trade_info)}")
            # self.metatrader_obj.sendOrder(trade_info)
            response = None
            update_event = self.process_edited_message(event,trade_info)
            if not update_event:
                response = requests.post(url=TRADE_URL,json=trade_info)
            else:
                logger.info(f"PUT Request updating the stack message store = {FXStreet.message_store}")
                trade_id = FXStreet.message_store[self.generate_key(trade_info)].pop()
                trade_info['trade_id'] = trade_id
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
                
                
    def generate_key(self,trade_info):
        return trade_info['currency'] + " " + trade_info['trade_type']
        
    def process_edited_message(self, event,trade_info):
        """Handles edited messages and checks if an important phrase was changed."""
        message_id = event.message.id  # Get message ID
        new_text = event.message.text  # New edited text
        ticket_ids = FXStreet.message_store[self.generate_key(trade_info)]
        if len(ticket_ids)!=0:
            return True
        return False
            
        
        # logger.info(f"edited Message id = {str(message_id)} Message content : [ {new_text} ]")
        # logger.info(f"Message store={str(FXStreet.message_store)}")
        # if len(FXStreet.message_store)!=0:
        #     old_text = new_text
        #     if message_id in FXStreet.message_store: # Check if we have the original message
        #         old_text = FXStreet.message_store[message_id]
        #     # If the original text contained "Gold Buy Now" or "Gold Sell Now", trigger alert
        #     if "gold buy now" in old_text or "gold sell now" in old_text:
        #         logger.info(f"Detected change in Gold trading message:\nOld: {old_text}\nNew: {new_text}")
        #         await self.process_messages(event,True)  # Call function if condition is met
        #     else:
        #         FXStreet.message_store.pop()
        #         await self.process_messages(event,False)
                
                
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
        currency = re.search(currency_pattern, message,re.IGNORECASE).group(1).strip().upper()
        trade_type = re.search(type_pattern, message,re.IGNORECASE).group(1).strip().upper()
        if not direct_order:
            entry_price = re.search(price_pattern, message,re.IGNORECASE).group(1).strip()
            entry_price2 = re.search(price_pattern, message,re.IGNORECASE).group(2).strip()
            sl = re.search(sl_pattern, message,re.IGNORECASE).group(1).strip()
            tp1 = re.search(tp1_pattern, message,re.IGNORECASE).group(1).strip()
            tp2 = re.search(tp2_pattern, message,re.IGNORECASE).group(1).strip()
        if currency == "XAUUSD":
            currency = "GOLD"
            
        if trade_type == "BUY NOW":
            trade_type = "BUY"
        elif trade_type == "SELL NOW":
            trade_type = "SELL"
        elif trade_type == "SELL ZONE":
            trade_type = "SELL"
        elif trade_type == "BUY ZONE":
            trade_type = "BUY"
            
            
        if entry_price2 is not None and len(entry_price2)!=0 :
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
            "time": event_time.strftime(TIME_FORMAT),
            "channel": "fxstreet"
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