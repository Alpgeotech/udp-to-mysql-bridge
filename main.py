

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        sys.exit

from classes import serial_transmitter
from classes import udp_receiver
from classes import data_tools


with open("config.toml", "rb") as f:
    config = tomllib.load(f)

general_settings_dict = config['general']


