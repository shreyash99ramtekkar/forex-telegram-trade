from logger.FxTelegramTradeLogger import FxTelegramTradeLogger
from notifications.Telegram import Telegram;
from service.TelegramApp import TelegramApp;
import threading;

fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)
telegram_app = TelegramApp();


telegram_obj = Telegram()

def main():
    try:
        with telegram_app.client:
            telegram_app.client.loop.run_until_complete(telegram_app.connect_and_listen())
        logger.info("Code ended gracefully")
        # with telegram_app.client:
        #     telegram_app.client.loop.run_until_complete(telegram_app.get_channel_id())
    except Exception as e:
        telegram_obj.sendMessage("Problem occured. App shutdown... Cause ["+ e.__cause__+"]")

if __name__ == "__main__":
    logger.info("Forex Telegram Trade application");
    main()
    