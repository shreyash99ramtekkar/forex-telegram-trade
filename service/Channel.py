from abc import ABCMeta,abstractmethod
from telethon import events

from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;
from notifications.Telegram import Telegram;
from constants.Constants import SYMBOL_URL;
import requests


fxstreetlogger = FxTelegramTradeLogger()

logger = fxstreetlogger.get_logger(__name__)


class Channel(metaclass=ABCMeta):  
    def __init__(self, client, telegram_obj):
        self.client = client
        self.telegram_obj = telegram_obj
        
    @abstractmethod
    async def connect_and_listen(self,CHANNEL_ID):
        # logger.info("Connecting to the telegram app");
        # await Channel.client.start()
        # logger.info("Connection successful");
        # Listen for new messages with specific keywords
        @self.client.on(events.NewMessage(chats=CHANNEL_ID))
        async def new_message_listener(event):
            await self.process_messages(event)  
        logger.info("Code ended gracefully")
        logger.info("Listening for filtered messages...")
        await self.client.run_until_disconnected()
    
    @abstractmethod
    def extract_trade_info(self,message,event_time,direct_order=False):
        """Extracts the Trade information from the message
        
        Keyword arguments:
        message -- The message recived on the telegram
        event_time -- The message received time on the telegram
        Return: json with the valid parameter {'currency': 'EURJPY', 'trade_type': 'SELL LIMIT', 'entry_price': '159.146', 'sl': '165.000', 'tp1': '158.500', 'tp2': '157.00', 'time': '2025-01-17 10:50:40'}
        """
        pass
    
    @abstractmethod
    def process_messages(self,event):
        """sumary_line
        
        Process the message according to the channel
        event -- Event information
        Return: return_description
        """
        
        pass
    
    @abstractmethod
    async def close_message_update(self,event):
        """Close the position as updated by the channel
        
        Keyword arguments:
        event -- Event information
        Return: return_description
        """
        pass
    
    def set_price(self, trade_info,sl_pip=50,tp_pip=20,tp2_pip=40,tp3_pip=100):
        THRESHOLD = 100
        logger.info(f"Received the request for updating the price in the trade info{str(trade_info)}")
        symbol = trade_info['currency']
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info is not None:
            point = symbol_info["point"] * 10   # Adjust pips calculation
            price = trade_info.get("entry_price")
            sl = trade_info.get("sl")
            tp = trade_info.get("tp1")
            tp2 = trade_info.get("tp2")
            tp3 = trade_info.get("tp3")
            type_ = trade_info.get("trade_type", "").upper()  # Ensure type is uppercase

            # If price, SL, TP, or TP2 is None, calculate defaults based on market price
                
            if type_ == "BUY":
                logger.info(f"Trade type is BUY")
                if price is None:
                    price = symbol_info["ask"]
                    logger.warn(f"Price is None. New price: {price}")
                    
                if tp is None or tp <= price or tp >= tp2 or abs(price - tp) > THRESHOLD:
                    logger.warn(f"Take profit 1 is None." if tp is None else f"tp {tp} <= price {price} OR tp {tp} >= tp2 {tp2} OR abs(price {price} - tp {tp}) > {THRESHOLD}")
                    tp = price + (tp_pip* point)
                    logger.info(f"New tp: {tp}")
                # Ensure TP3 is set first because it will be always set to OPEN(None) and for next comparison(tp2>=tp3) we need tp3 set
                if tp3 is None or tp3 <= tp2 or abs(tp3 - price) > THRESHOLD:
                    logger.warn(f"Tp3 {tp3} <= tp2 {tp2} or abs(tp3 {tp3} - price {price}) > {THRESHOLD}." if tp3 is not None else f"Take profit 3 is None.")
                    tp3 =  price + (tp3_pip * point)
                    logger.info(f"New tp3: {tp3}")
                             
                if tp2 is None or (tp2 <= tp) or (tp2 >= tp3) or abs(tp2 - price) > THRESHOLD:
                    logger.warn(f"(tp2 {tp2} <= tp {tp}) or (tp2 {tp2} >= tp3 {tp3}) or abs(tp2 {tp2} - price {price}) > {THRESHOLD}" if tp2 is not None else f"Take profit 2 is None.")
                    tp2 = price + (tp2_pip * point)
                    logger.info(f"New tp2: {tp2}")
                    
                # if sl is None or sl >= price or abs(price - sl) >  THRESHOLD:
                #     logger.warn(f"Sl {sl} >= price {price} OR abs(price {price} - sl {sl}): { abs(price - sl) } > 20" if sl is not None else f"Stop loss is None.")
                sl = price - (sl_pip * point) 
                logger.info(f"New sl: {sl}")
            else:
                logger.info(f"Trade type is SELL")
                if price is None:
                    price = symbol_info["bid"]
                    logger.info(f"Price is None. Using bid price: {price}")
                    
                if tp is None or tp >= price or tp <= tp2 or abs(price - tp) > THRESHOLD:
                    logger.warn(f"Take profit 1 is None." if tp is None else f"tp {tp} >= price {price} OR tp {tp} <= tp2 {tp2} OR abs(price {price} - tp {tp}) > {THRESHOLD}")
                    tp = price - (tp_pip * point)
                    logger.info(f"New tp: {tp}")
                    
                # Ensure TP3 is set first because it will be always set to OPEN(None) and for next comparison(tp2>=tp3) we need tp3 set
                if tp3 is None or tp3 >= tp2 or abs(tp3 - price) > THRESHOLD:
                    logger.warn(f"Tp3 {tp3} >= tp2 {tp2} or abs(tp3 {tp3} - price {price}) > {THRESHOLD}." if tp3 is not None else f"Take profit 3 is None.")
                    tp3 = price - (tp3_pip * point)
                    logger.info(f"New tp3: {tp3}")
                   
                if tp2 is None or (tp2 >= tp) or (tp2 <= tp3) or abs(tp2 - price) > THRESHOLD:
                    logger.warn(f"(tp2 {tp2} >= tp {tp}) or (tp2 {tp2} <= tp3 {tp3}) or abs(tp2 {tp2} - price {price}) > {THRESHOLD}" if tp2 is not None else f"Take profit 2 is None.")
                    tp2 = price - (tp2_pip * point)
                    logger.info(f"New tp2: {tp2}")
                    
                # if sl is None or sl <= price or abs(sl - price) > 20:
                #     logger.warn(f"Sl {sl} <= price {price} OR abs(price {price} - sl {sl}): {abs(price - sl) } > 20" if sl is not None else f"Stop loss is None.")
                sl = price + (sl_pip * point)
                logger.info(f"New sl: {sl}")
             # ✅ Update trade_info with new values
            trade_info.update({
                "entry_price": price,
                "sl": sl,
                "tp1": tp,
                "tp2": tp2,
                "tp3": tp3
            })
            logger.info(f"updated trade info object {str(trade_info)}")
        else:
            logger.error(f"Failed to fetch symbol info for {symbol}.")
       
        return trade_info
    
    def get_symbol_info(self,symbol):
        symbol_info = None
        response = requests.get(url=SYMBOL_URL+"/"+symbol)
        if response.status_code == 200:
            symbol_info = response.json() 
            # Ensure required keys exist
            if "point" not in symbol_info or "ask" not in symbol_info or "bid" not in symbol_info:
                logger.error(f"Missing required fields in symbol_info: {symbol_info}")
                return  # Exit function
            logger.info(f"Received symbol info object {str(symbol_info)}")
        else:
            logger.warn(f"Failed to fetch symbol info for {symbol}. Response: {response.status_code}, {response.text}")
        return symbol_info
            

       
        
        
    def delta_order(self,trade_info,pips=50):
        
        symbol = trade_info['currency']
        if symbol != "GOLD":
            pips = 20
        logger.info(f"Received the request for delta trade with difference of {pips} pips for symbol {symbol}")
        response = requests.get(url=SYMBOL_URL+"/"+symbol)
        if response.status_code == 200:
            symbol_info = response.json()     
            # Ensure required keys exist
            if "point" not in symbol_info or "ask" not in symbol_info or "bid" not in symbol_info:
                logger.error(f"Missing required fields in symbol_info: {symbol_info}")
                return  # Exit function
            point = symbol_info["point"] * 10 * pips  # Adjust pips calculation

             # Extract trade parameters
            price = trade_info.get("entry_price")
            sl = trade_info.get("sl")
            tp = trade_info.get("tp1")
            tp2 = trade_info.get("tp2")
            tp3 = trade_info.get("tp3")
            type_ = trade_info.get("trade_type", "").upper()
            
            # Adjust price, SL, TP, TP2 based on trade type
            if type_ == "BUY":
                price -= point
                sl -= point
                tp -= point
                tp2 -= point
                tp3 -= point
            elif type_ == "SELL":
                price += point
                sl += point
                tp += point
                tp2 += point
                tp3 += point

            # ✅ Update trade_info with new values
            trade_info.update({
                "entry_price": price,
                "sl": sl,
                "tp1": tp,
                "tp2": tp2,
                "tp3": tp3
            })
            logger.info(f"Updated trade_info for delta order: {str(trade_info)}")
        else:
            logger.error(f"Failed to fetch symbol info for {symbol}. Response: {response.status_code}, {response.text}")
        
    
    async def get_channel_id(self):
        # Connect to the Telegram client
        await self.client.start()
        # Iterate through all dialogs to list their names and IDs
        async for dialog in self.client.iter_dialogs():
            # Print the name and ID of each chat
            logger.info(f"Name: {dialog.name}, ID: {dialog.id}")

    def safe_float(self,value):
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None  # or return a default value