from logger.FxTelegramTradeLogger import FxTelegramTradeLogger
from notifications.Telegram import Telegram;
from service.TradeTiten import TradeTiten
from service.FXStreet import FXStreet


fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)


telegram_obj = Telegram()
trade_titen = FXStreet()

def main():
    try:
        with trade_titen.client:
            trade_titen.client.loop.run_until_complete(trade_titen.connect_and_listen())
        logger.info("Code ended gracefully")
        # with telegram_app.client:
        #     telegram_app.client.loop.run_until_complete(telegram_app.get_channel_id())
    except Exception as e:
        print(e)
        telegram_obj.sendMessage("Problem occured. App shutdown... Cause ["+ str(e.__cause__)+"]")

if __name__ == "__main__":
    logger.info("Forex Telegram Trade application");
    main()
    