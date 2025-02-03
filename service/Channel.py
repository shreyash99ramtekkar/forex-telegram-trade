from abc import ABCMeta,abstractmethod
from telethon import TelegramClient, events
from constants.TelegramConstants import TELEGRAM_APP_ID
from constants.TelegramConstants import TELEGRAM_SESSION;
from constants.TelegramConstants import TELEGRAM_HASH_ID
from logger.FxTelegramTradeLogger import FxTelegramTradeLogger;
from notifications.Telegram import Telegram;


fxstreetlogger = FxTelegramTradeLogger()

logger = fxstreetlogger.get_logger(__name__)


class Channel(metaclass=ABCMeta):  
    client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_APP_ID, TELEGRAM_HASH_ID) 
    telegram_obj = Telegram() 
        
    @abstractmethod
    async def connect_and_listen(self):
        pass
    
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
    
    async def get_channel_id(self):
        # Connect to the Telegram client
        await self.client.start()
        # Iterate through all dialogs to list their names and IDs
        async for dialog in self.client.iter_dialogs():
            # Print the name and ID of each chat
            logger.info(f"Name: {dialog.name}, ID: {dialog.id}")

    