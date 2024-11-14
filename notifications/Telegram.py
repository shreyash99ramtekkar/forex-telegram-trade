
import requests
from constants.TelegramConstants import TELEGRAM_TOKEN;
from constants.TelegramConstants import TELEGRAM_CHAT_ID;

from logger.FxTelegramTradeLogger import FxTelegramTradeLogger

fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)

class Telegram:
    def __init__(self):
        self.token = TELEGRAM_TOKEN;
        self.chat_id= TELEGRAM_CHAT_ID
        self.base_url = "https://api.telegram.org/bot" + self.token 
    
    def sendMessage(self,message):
        url = self.base_url + "/sendMessage?chat_id=" + self.chat_id + "&text=" + message 
        logger.debug(requests.get(url).json()) # this sends the message

    def sendImageCaption(self,image_file,message):
        url = self.base_url+"/sendPhoto"
        parameters = {
                "chat_id": self.chat_id,
                "caption": message
            }
        resp = requests.get(url,params=parameters,files=image_file)
        logger.debug(resp.text)