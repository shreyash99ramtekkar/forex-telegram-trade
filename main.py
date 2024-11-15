from logger.FxTelegramTradeLogger import FxTelegramTradeLogger
from notifications.Telegram import Telegram;
from model.TelegramApp import TelegramApp;
from model.MetatraderSocket import MetatraderSocket
from notifications.Telegram import Telegram;

fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)
socket = MetatraderSocket()
telegram_app = TelegramApp(socket);


telegram_obj = Telegram()

def main():
    
    
    try:
        # with telegram_app.client:
        #     logger.info("Telegram APP client initialized");
        #     telegram_app.client.loop.run_until_complete(telegram_app.fetch_last_message())
        with telegram_app.client:
            telegram_app.client.loop.run_until_complete(telegram_app.connect_and_listen())
        # with telegram_app.client:
        #     telegram_app.client.loop.run_until_complete(telegram_app.get_channel_id())
    except Exception as e:
        telegram_obj.sendMessage("Problem occured. App shutdown... Cause ["+ e.__cause__+"]")
    finally:
        logger.info("Closing the connection for the metatrader5");
        socket.close_connection()


if __name__ == "__main__":
    logger.info("Forex Telegram Trade application");
    main()
    