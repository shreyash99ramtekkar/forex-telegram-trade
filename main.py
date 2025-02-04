from logger.FxTelegramTradeLogger import FxTelegramTradeLogger
from notifications.Telegram import Telegram;
from service.TradeTiten import TradeTiten
from service.FXStreet import FXStreet
from service.Channel import Channel
import asyncio
from constants.TelegramConstants import FX_STREET_TELE_IDS
from constants.TelegramConstants import TRADE_TITEN_TELE_IDS
from constants.TelegramConstants import TELEGRAM_APP_ID
from constants.TelegramConstants import TELEGRAM_SESSION;
from constants.TelegramConstants import TELEGRAM_HASH_ID
from telethon import TelegramClient, events
fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)

client = TelegramClient(TELEGRAM_SESSION, TELEGRAM_APP_ID, TELEGRAM_HASH_ID) 
telegram_obj = Telegram() 
trade_titen = TradeTiten(client,telegram_obj)
fx_street = FXStreet(client,telegram_obj)

# Main method to run both channels
async def main():
    try:
        await client.start()
        # Run both channels concurrently using asyncio.gather
        await asyncio.gather(
            trade_titen.connect_and_listen(TRADE_TITEN_TELE_IDS),
            fx_street.connect_and_listen(FX_STREET_TELE_IDS)
        )
    except Exception as e:
        print(e)
        telegram_obj.sendMessage("Problem occured. App shutdown... Cause ["+ str(e.__cause__)+"]")
if __name__ == "__main__":
    logger.info("Forex Telegram Trade application");
    asyncio.run(main())
    