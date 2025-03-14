import os
from dotenv import load_dotenv
load_dotenv()
MT5_API_SERVER = os.getenv("MT5-API-SERVER")
MT5_API_PORT = os.getenv("MT5-API-PORT")

TRADE_URL = "http://" + MT5_API_SERVER + ":" +MT5_API_PORT+"/trade"
SYMBOL_URL = "http://" + MT5_API_SERVER + ":" +MT5_API_PORT+"/symbol"


TIME_FORMAT = "%Y-%m-%d %H:%M:%S"