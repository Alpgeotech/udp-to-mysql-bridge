import socket as s
import logging
import time

MAX_ETHERNET_FRAME_SIZE = 1500

logger = logging.getLogger(__name__)

class UdpReceiver:
   
    def __init__(self, udp_settings_dict:dict) -> None:
        self.settings = udp_settings_dict
        self.sock = s.socket(s.AF_INET, s.SOCK_DGRAM)
        self.sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        self.__update_udp_last_seen_file_for_rsh_watchdog()
        self.__wait_for_network()

    def __udp_port_usable(self):
        try:
            self.sock.bind((self.settings['ip_address'], int(self.settings['port'])))
            logger.info(f'Bound to socket {self.settings["ip_address"]}:{self.settings["port"]}')
            return True
        except OSError:
            logger.exception("Exception details:")
        return False
    
    def __wait_for_network(self, timeout=60):
        start_time = time.time()
        while not self.__udp_port_usable():
            if time.time() - start_time > timeout:
                logger.error("Network did not initialize within timeout. Exiting.")
                raise RuntimeError("Network initialization timed out")
            logger.warning("Network not initialized, retrying in 5 seconds...")
            time.sleep(5)

    def read(self):
        try:
            data = self.sock.recv(MAX_ETHERNET_FRAME_SIZE)
            data = data.decode('UTF-8')
            logger.debug(data)
            self.__update_udp_last_seen_file_for_rsh_watchdog()
            return data
        except UnicodeDecodeError as e:
            logger.error("Decoding error while reading UDP packet.")
            logger.exception("Exception details:")
            return None
        except OSError as e:
            logger.error("Socket read error.")
            logger.exception("Exception details:")
            return None
        except Exception as e:
            logger.exception("Exception details:")
            return None
    
    def __update_udp_last_seen_file_for_rsh_watchdog(self):
        try:
            with open(self.settings['udp_last_seen_file'], "w") as f:
                f.write(str(time.time()))
        except Exception as e:
            logger.error(f"Failed to write last seen timestamp: {e}")

    def close(self):
        self.sock.close()
        logger.debug("Socket closed.")
