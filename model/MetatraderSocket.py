from mt5linux import MetaTrader5
from constants.MetatraderConstants import METATRADER_ACCOUNT_ID
from constants.MetatraderConstants import METATRADER_BROKER_SERVER
from constants.MetatraderConstants import METATRADER_PASSWORD
from logger.FxTelegramTradeLogger import FxTelegramTradeLogger
import os
import math
from time import sleep

from notifications.Telegram import Telegram;

telegram_obj = Telegram()

fxstreetlogger = FxTelegramTradeLogger()
logger = fxstreetlogger.get_logger(__name__)

class MetatraderSocket:
    def __init__(self):
        logger.info(os.getenv("MT5_SERVER") + " port: "+ str(os.getenv("MT5_PORT")))
        # connecto to the server
        self.mt5 = MetaTrader5(
            host = os.getenv("MT5_SERVER"),
            port = os.getenv("MT5_PORT")
        ) 
        
        # use as you learned from: https://www.mql5.com/en/docs/integration/python_metatrader5/
        if not self.mt5.initialize():
            logger.error("initialize() failed, error code =",self.mt5.last_error())
            telegram_obj.sendMessage("Problem connecting to Metatrader5" + self.mt5.last_error())
        self.mt5.terminal_info()

        


    def get_rates(self):
        df = self.mt5.copy_rates_from_pos('EURUSD',self.mt5.TIMEFRAME_M30,0,1000)
        # ...
        # don't forget to shutdown
        logger.debug(df)

    def check_n_get_order_type(self,symbol_info,type,price):
        """Check the prices from the vip channel match the symbol current price .if not then its a limit order"""
        if (type == "buy" or type == "buy now") and  math.floor(price) != math.floor(symbol_info.ask):
            logger.info(f"The price [{math.floor(symbol_info.ask)}] doesn't match the telegram price [{math.floor(price)}]: Limit Order BUY")
            return "buy limit"
        elif (type == "sell" or type == "sell now") and  math.floor(price) != math.floor(symbol_info.bid):
            logger.info(f"The price [{math.floor(symbol_info.bid)}] doesn't match the telegram price [{math.floor(price)}]: Limit Order SELL")
            return "sell limit"
        logger.info(f"The price match the telegram price [{price}]: {type}")
        telegram_obj.sendMessage(f"The order type is: [{type}]")
        return type;

    def sendOrder(self,message):
        symbol = message['currency']
        type_ = message['trade_type']
        sl = float(message['sl'])
        tp = float(message['tp1'])
        tp2 = float(message['tp2'])
        action_ = None;
        price = float(message['entry_price'])
        if len(symbol) == 0 or len(type_) == 0 or sl is None or tp is None or price is None:
            logger.warning("Cannot proceed. The trade info not sufficient to make a trade")
            return;
        if symbol == "XAUUSD":
            symbol="GOLD"
        symbol_info = self.mt5.symbol_info(symbol)
        type_ = self.check_n_get_order_type(symbol_info,type_,price)
        logger.debug(symbol_info.volume_min)
        # lot = 0.02;   
        lot = symbol_info.volume_min;   
        deviation = 40
        
        if "buy limit" in type_.lower():
            action_ = self.mt5.TRADE_ACTION_PENDING;
            type_ = self.mt5.ORDER_TYPE_BUY_LIMIT
        elif "buy now" in type_.lower() or "buy" in type_.lower():
            action_ = self.mt5.TRADE_ACTION_DEAL;
            type_ = self.mt5.ORDER_TYPE_BUY
            price = symbol_info.ask
        elif "sell limit" in type_.lower():
            action_ = self.mt5.TRADE_ACTION_PENDING;
            type_ = self.mt5.ORDER_TYPE_SELL_LIMIT
        elif "sell now" in type_.lower() or 'sell' in type_.lower():
            action_ = self.mt5.TRADE_ACTION_DEAL;
            type_ = self.mt5.ORDER_TYPE_SELL
            price = symbol_info.bid
        else:
            logger.warning("Type not valid please check the code");
            telegram_obj.sendMessage("Type not valid.")
            return
   
        if action_ is None:
            logger.warning("Action is None cannot proceed")
            return;
        telegram_obj.sendMessage(f"Currency: [{message['currency']}], type: [{type_}] SL: {sl}, TP: {tp} Action: {action_}" )
        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            logger.info(symbol+ "is not visible, trying to switch on")
            if not self.mt5.symbol_select(symbol,True):
                logger.warning("symbol_select({}}) failed, exit" + symbol)

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
            "comment": str(tp2),
            "type_time": self.mt5.ORDER_TIME_GTC
            # "type_filling": self.mt5.ORDER_FILLING_IOC,
        }
        
        logger.info("The request is ["+str(request)+"]")
        # send a trading request
        if (self.checkOldPosition()) or (self.checkOldPositionSymbol(symbol)) :
            return
        result = self.mt5.order_send(request)
        logger.info(f"The result from metatrader5 : {str(result)}")
        # check the execution result
        logger.info("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol,lot,price,deviation));
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logger.error("2. order_send failed, retcode={}, Reason={}".format(result.retcode,result.comment))
            telegram_obj.sendMessage("Order failed..." + str(result.comment))
            # request the result as a dictionary and display it element by element
            result_dict=result._asdict()
            for field in result_dict.keys():
                # logger.error("   {}={}".format(field,result_dict[field]))
                # if this is a trading request structure, display it element by element as well
                if field=="request":
                    traderequest_dict=result_dict[field]._asdict()
                    logger.error(f"traderequest: {str(traderequest_dict)}")
                    # for tradereq_filed in traderequest_dict:
                    #     logger.error("traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))

    def checkOldPositionSymbol(self,symbol):
        threshold = 2
        orders=self.mt5.positions_get(symbol=symbol)
        if orders is None:
            logger.info("No orders on ["+ symbol +"] error code={}".format(self.mt5.last_error()))
            return False;
        else:
            logger.info("Open orders for the symbol " + symbol + " are " )
            for order in orders:
                logger.info(order)
            if len(orders)<threshold:
                logger.info(f"Open orders on currency [{symbol}] are [{len(orders)}] which is less than Threshold [{threshold}]")
                return False;
            logger.warning("Already open position on the symbol")
            logger.info(f"Total orders on [{symbol}] : {str(len(orders))} which is more than Threshold [{threshold}]")
            telegram_obj.sendMessage(f"Total orders on [{symbol}] : {str(len(orders))} which is more than Threshold [{threshold}]. Please take the action on the open orders")
        return True;

    def checkOldPosition(self):
        threshold = 3
        orders=self.mt5.positions_get()
        if orders is None:
            logger.info("No open orders error code={}".format(self.mt5.last_error()))
            return False;
        else:
            logger.info("Open orders are " )
            for order in orders:
                logger.info(order)
            if len(orders)>=threshold:
                logger.info(f"Open orders are [{len(orders)}] which is more than Threshold [{threshold}]")
                telegram_obj.sendMessage(f"Total orders : {str(len(orders))} which is more than Threshold [{threshold}]. Please take the action on the open orders")
                return True;
            else:
                return False

    def monitor_close_half_update_tp(self):
        """Monitor the open trades, Close half of the open positions and update the tp to new tp"""
        # Monitor trades and perform updates
        while True:
            positions = self.mt5.positions_get()
            if positions is None:
                logger.info("No open positions or error:", mt5.last_error())
                continue

            for position in positions:
                # Extract trade details
                ticket = position.ticket
                symbol = position.symbol
                entry_price = position.price_open
                volume = position.volume
                comment = position.comment
                tp1 = position.tp
                type_ = position.type
                if self.is_float(comment):
                    tp2 = float(comment)
                else:
                    continue;

                # Current market price
                current_price = self.mt5.symbol_info_tick(symbol).bid if position.type == self.mt5.ORDER_TYPE_SELL else self.mt5.symbol_info_tick(symbol).ask
                logger.info(f"The open position [{ticket}] of symbol [{symbol}]  of  type {type_} is having difference of {abs(current_price - tp1)} pips. Current price: [{current_price}] tp1: [{tp1}]")
                # Check if the price is approaching TP1 (within 2-3 pips)
                if abs(current_price - tp1) <= 0.50:  # Assuming 5-digit broker, adjust as needed
                    # Move SL to entry price and TP to TP2
                    self.modify_trade(ticket,symbol, new_sl=entry_price, new_tp=tp2)
                    # Close half the position
                    self.close_half_position(ticket, symbol, type_, volume)
            logger.debug("Sleeping for 5 seconds")
            sleep(2)  # Avoid overloading the terminal

    def is_float(self,string):
        try:
        # Return true if float
            float(string)
            return True
        except ValueError:
        # Return False if Error
            return False

    def modify_trade(self,ticket,symbol, new_sl, new_tp):
        request = {
            "action": self.mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": new_sl,
            "tp": new_tp,
        }
        logger.info(f"The modify request is {str(request)}")
        result = self.mt5.order_send(request)
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logger.info(f"Failed to modify trade {ticket}: {result.comment}")
        else:
            logger.info(f"Trade {ticket} modified: SL={new_sl}, TP={new_tp}")
            telegram_obj.sendMessage(f"Trade updated for [{symbol}]. Tread.")

    # Close half of the trade volume
    def close_half_position(self,ticket, symbol, position_type, volume):
        # MetaTrader 5 minimum lot size (typically 0.01, but can vary by broker)
        MIN_VOLUME = 0.01

        # If the current volume is the minimum, close the entire position
        if volume <= MIN_VOLUME:
            logger.info(f"Volume {volume} is too small to close half. Closing the entire position.")
            half_volume = volume  # Close the full position
        else:
            # Calculate half volume and ensure it's at least MIN_VOLUME
            half_volume = max(volume / 2, MIN_VOLUME)

         # Determine the counter-order type
        counter_order_type = self.mt5.ORDER_TYPE_BUY if position_type == self.mt5.ORDER_TYPE_SELL else self.mt5.ORDER_TYPE_SELL

        # Calculate the price based on the counter-order type
        price = self.mt5.symbol_info_tick(symbol).ask if counter_order_type == self.mt5.ORDER_TYPE_BUY else self.mt5.symbol_info_tick(symbol).bid

        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": half_volume,
            "type": counter_order_type,
            "position": ticket,
            "price": price,
            "deviation": 10,
        }
        result = self.mt5.order_send(request)
        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            logger.info(f"Failed to close half of the trade {ticket}: {result.comment}")
        else:
            logger.info(f"Half of the currency [{symbol}] trade {ticket} closed: {volume}")

    def close_connection(self):
        self.mt5.shutdown()