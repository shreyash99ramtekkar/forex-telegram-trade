from mt5linux import MetaTrader5
from constants.MetatraderConstants import METATRADER_ACCOUNT_ID
from constants.MetatraderConstants import METATRADER_BROKER_SERVER
from constants.MetatraderConstants import METATRADER_PASSWORD
from logger.FxTelegramTradeLogger import FxTelegramTradeLogger
from notifications.Telegram import Telegram;

fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)

class MetatraderSocket:
    def __init__(self):
        # import the package

        # connecto to the server
        self.mt5 = MetaTrader5(
            host = 'localhost',
            port = 8001
        ) 
        
        # use as you learned from: https://www.mql5.com/en/docs/integration/python_metatrader5/
        if not self.mt5.initialize():
            logger.error("initialize() failed, error code =",self.mt5.last_error())
       
        self.mt5.terminal_info()

        self.telegram_obj = Telegram()


    def get_rates(self):
        df = self.mt5.copy_rates_from_pos('EURUSD',self.mt5.TIMEFRAME_M30,0,1000)
        # ...
        # don't forget to shutdown
        print(df)


    def sendOrder(self,message):
        symbol = message['currency']
        type_ = message['trade_type']
        sl = float(message['sl'])
        tp = float(message['tp1'])
        action_ = None;
        price = float(message['entry_price'])
        if len(symbol) == 0 or len(type_) == 0 or sl is None or tp is None or price is None:
            logger.warning("Cannot proceed. The trade info not sufficient to make a trade")
            return;
        if symbol == "XAUUSD":
            symbol="GOLD"
        print(self.mt5.symbol_info(symbol).volume_min)
        lot = self.mt5.symbol_info(symbol).volume_min;   
        deviation = 40
        self.telegram_obj.sendMessage(str(message))
        if "buy limit" in type_.lower():
            action_ = self.mt5.TRADE_ACTION_PENDING;
            type_ = self.mt5.ORDER_TYPE_BUY_LIMIT
        elif "buy now" in type_.lower():
            action_ = self.mt5.TRADE_ACTION_DEAL;
            type_ = self.mt5.ORDER_TYPE_BUY
            price = self.mt5.symbol_info_tick(symbol).ask
        elif "sell limit" in type_.lower():
            action_ = self.mt5.TRADE_ACTION_PENDING;
            type_ = self.mt5.ORDER_TYPE_SELL_LIMIT
        elif "sell now" in type_.lower():
            action_ = self.mt5.TRADE_ACTION_DEAL;
            type_ = self.mt5.ORDER_TYPE_SELL
            price = self.mt5.symbol_info_tick(symbol).bid
        else:
            logger.warning("Type not valid please check the code");
            self.telegram_obj.sendMessage("Type not valid.")
            return
        
        if action_ is None:
            logger.warning("Action is None cannot proceed")
            return;

        request = {
            "action": action_,
            "symbol": symbol,
            "volume": lot,
            "type": type_,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "magic": 77777,
            "comment": "python script open",
            "type_time": self.mt5.ORDER_TIME_GTC
            # "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        logger.info(request)
        # send a trading request
        if self.checkOldPositionSymbol(symbol) and self.checkOldPosition():
            return
        result = self.mt5.order_send(request)
        print(result)
        # check the execution result
        logger.info("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol,lot,price,deviation));
        logger.info(result)
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logger.error("2. order_send failed, retcode={}".format(result.retcode))
            # request the result as a dictionary and display it element by element
            result_dict=result._asdict()
            for field in result_dict.keys():
                logger.error("   {}={}".format(field,result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field=="request":
                    traderequest_dict=result_dict[field]._asdict()
                    for tradereq_filed in traderequest_dict:
                        logger.error("traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))


    def checkOldPositionSymbol(self,symbol):
        orders=self.mt5.positions_get(symbol=symbol)
        if orders is None:
            logger.info("No orders on ++"+ symbol +" error code={}".format(self.mt5.last_error()))
            return False;
        else:
            if len(orders)==0:
                logger.info("No orders on : "+ symbol)
                return False;
            logger.warning("Already open position on the symbol")
            logger.info("Total orders on "+ symbol + ":" + str(len(orders)))
            self.telegram_obj.sendMessage("Already open position on the "+ str(symbol) +". Please take the action on the open orders")
        # display all active orders
        logger.info("Open orders for the symbol " + symbol + " are " )
        for order in orders:
            logger.info(order)
        return True;

    def checkOldPosition(self):
        threshold = 1
        orders=self.mt5.positions_get()
        if orders is None:
            logger.info("No open orders error code={}".format(self.mt5.last_error()))
            return False;
        else:
            logger.info("Open orders are " )
            for order in orders:
                logger.info(order)
            if len(orders)>=threshold:
                logger.info("Equal or More than " + str(threshold) + " orders open")
                self.telegram_obj.sendMessage("Already more than " + str(threshold) + " position open. So not executing the 3rd trade")
                return True;
            else:
                return False

    def close_connection(self):
        self.mt5.shutdown()