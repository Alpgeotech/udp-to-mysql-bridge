import os
import sys
import time
import logging
import serial
import serial.tools.list_ports

import time
import queue
import threading

logger = logging.getLogger(__name__)

class SerialDeviceError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class Transmitter():
    def __init__(self, serial_settings:dict) -> None:
        self.settings = serial_settings

    def open_serial_connection(self):
        raise NotImplementedError()

    def enqueue_message(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class ConsoleTransmitter(Transmitter):
    def __init__(self, serial_settings:dict) -> None:
        super().__init__(serial_settings)
        self._isStopRequested = False
        self._reader_thread = threading.Thread(target=self.__read_from_stdin, daemon=True)
        self._reader_thread.start()

    def open_serial_connection(self):
        logger.info("ConsoleTransmitter up and running.")

    def enqueue_message(self,message):
        print(message)
        logger.info("Message printed to console.")
        logger.debug(message)

    def __read_from_stdin(self):
        logger.info("ConsoleTransmitter read thread started. Type to emulate serial input.")
        while not self._isStopRequested:
            try:
                line = sys.stdin.readline()
                if not line:
                    continue
                line = line.strip()
                if "rsh-reboot" in line.lower():
                    logger.info("Reboot command received via console.")
                    # Emulate action (don't reboot real device!)
                    print("[ConsoleTransmitter] Emulated reboot triggered.")
            except Exception as e:
                logger.exception("Error reading from stdin")

    def close(self):
        self._isStopRequested = True


class SerialTransmitter(Transmitter):

    def __init__(self, serial_settings:dict) -> None:
        super().__init__(serial_settings)
        self._connectionState = "never"
        self._queue = queue.SimpleQueue()

        self._isStopRequested = False
        self._reader_thread = threading.Thread(target=self.__read_from_serial, daemon=True)
        self._writer_thread = threading.Thread(target=self.__write_to_serial, daemon=True)
        self._reader_thread.start()
        self._writer_thread.start()

    def __find_serial_device(self, vid, pid):
        """
        Find the serial device matching the given Vendor ID (VID) and Product ID (PID).
        :param vid: Vendor ID (Hex format or int)
        :param pid: Product ID (Hex format or int)
        :return: Device name (Linux: /dev/tty*, Windows: COMx) or None if not found
        """

        vid = int(vid, base=16) if isinstance(vid, str) else vid
        pid = int(pid, base=16) if isinstance(pid, str) else pid

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.vid == vid and port.pid == pid:
                logger.info(f"serial_device: {port.device}")
                return port.device  # Returns /dev/ttyUSBx on Linux, COMx on Windows

        message = f"Cannot find device with vid {vid} and pid {pid}."
        logger.error(message)
        raise SerialDeviceError(message)

    def __construct_serial_connection(self):
        self.serial_device = self.__find_serial_device(self.settings['vendor_id'], self.settings['product_id'])
        ser = serial.serial_for_url(self.serial_device, do_not_open=True)
        ser.baudrate = int(self.settings['baudrate'])
        ser.bytesize = int(self.settings['bytesize'])
        ser.parity = self.settings['parity']
        ser.stopbits = int(self.settings['stopbits'])
        ser.timeout = None
        return ser

    def __open_serial_connection(self):
        try:
            # Close existing connection if already open
            if hasattr(self, 'ser') and self.ser and self.ser.is_open:
                self.ser.close()
                logger.info("Existing serial connection closed before reopening.")

            # Construct and open a fresh connection
            self.ser = self.__construct_serial_connection()
            self.ser.open()
            logger.info("Serial connection is up and running!")
            self._connectionState = "up"
        except:
            self._connectionState = "down"
            logger.warning("Cannot open serial port! Ignoring!")
            time.sleep(1)

    def enqueue_message(self, message):
        self._queue.put(message)
        logger.debug("Message put in transmission queue.")

    def time_since_last_transmission(self):
        return time.time(time) - self._timestamp_of_last_transmission

    def __write_to_serial(self):
        current_message = None

        while not self._isStopRequested:
            if self._connectionState == 'up':
                try:
                    if current_message is None:
                        current_message = self._queue.get(block=True, timeout=None)
                        
                    self.ser.write(current_message.encode())
                    logger.info('Message written to serial connection.')
                    logger.debug(current_message)

                    current_message = None
                    # time.sleep(self.settings['min_time_between_transmissions'])
                except Exception as e:
                    logger.error(f'Cannot write to serial device.')
                    logger.exception(e)
                    self._connectionState = 'down'

            else:
                self.__open_serial_connection()
        
        if self.ser:
            self.ser.close()

    def __read_from_serial(self):
        while not self._isStopRequested:
            if self._connectionState == "up":
                try:
                    # Adjust timeout in serial port setup if needed
                    line = self.ser.readline().decode(errors="ignore").strip()
                    logger.warning("Command received via serial connection.")
                    logger.warning(line)
                    if "rsh-reboot" in line.lower():
                        logger.info("Reboot command received over serial.")
                        os.system("/usr/local/bin/rsh-reboot")
                except Exception as e:
                    logger.error("Cannot read from serial device.")
                    logger.exception(e)
                    self._connectionState = "down"
            else:
                time.sleep(1)  # Give time before retrying

    def close(self):
        self.isStopRequested = True
        