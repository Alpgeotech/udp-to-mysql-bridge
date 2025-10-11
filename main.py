import sys
import os
import logging
import logging.handlers

from classes import mysql

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        sys.exit

# from classes import serial_transmitter
from classes import udp_receiver


with open("config.toml", "rb") as f:
    config = tomllib.load(f)

general_settings_dict = config['general']
mysql_settings_dict = config['mysql']
udp_settings_dict = config['udp']


log_location = general_settings_dict.get("log_location", "./log")
if not os.path.exists(log_location):
    os.mkdir(log_location)

logger = logging.getLogger()
logger.setLevel(general_settings_dict.get("log_level", "INFO").upper())

formatter = logging.Formatter(
    "[%(levelname)-7s] [%(asctime)s] %(name)10s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler = logging.handlers.RotatingFileHandler(
    f"{log_location}/udp_to_serial.log", maxBytes=(1048576*5), backupCount=7, encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream handler (stdout -> captured by systemd)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler.doRollover()

# Catch unhandled exceptions in main thread
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Let KeyboardInterrupt go through without logging
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

logger.warning("=========== NEW START OF udp-to-serial-converter ===========")

receiver = udp_receiver.UdpReceiver(udp_settings_dict)
database_caller = mysql.MySql(mysql_settings_dict)


try: 
    while 1:
        dataset = receiver.read()
        print(dataset)
        #TODO: parse data here


        # database_caller.insertDataset(dataset)

finally:
    receiver.close()
    # transmitter.close()
    

