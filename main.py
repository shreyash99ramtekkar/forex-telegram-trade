from logger.FxTelegramTradeLogger import FxTelegramTradeLogger
from notifications.Telegram import Telegram;
from model.TelegramApp import TelegramApp;
from model.MetatraderSocket import MetatraderSocket
from notifications.Telegram import Telegram;
import threading;

fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)
socket = MetatraderSocket()
telegram_app = TelegramApp(socket);


telegram_obj = Telegram()

def main():
    
    
    try:
        start_monitoring()
        # with telegram_app.client:
        #     logger.info("Telegram APP client initialized");
        #     telegram_app.client.loop.run_until_complete(telegram_app.fetch_last_message())
        with telegram_app.client:
            telegram_app.client.loop.run_until_complete(telegram_app.connect_and_listen())
        logger.info("Code ended gracefully")
        # with telegram_app.client:
        #     telegram_app.client.loop.run_until_complete(telegram_app.get_channel_id())
    except Exception as e:
        telegram_obj.sendMessage("Problem occured. App shutdown... Cause ["+ e.__cause__+"]")
    finally:
        logger.info("Closing the connection for the metatrader5");
        socket.close_connection()


def start_monitoring():
    monitor_thread = threading.Thread(target=socket.monitor_close_half_update_tp, name="OpenPositionMonitor")
    monitor_thread.daemon = True  # Allows the thread to exit when the main program does
    monitor_thread.start()
    logger.info("Monitoring thread started.")

if __name__ == "__main__":
    logger.info("Forex Telegram Trade application");
    main()
    