import pymysql.cursors

import logging

logger = logging.getLogger(__name__)


class MySql:
    def __init__(self, mySqlSettingsDict):
        self.__connectionState = "never"
        self.hostAddress = mySqlSettingsDict["host_address"]
        self.portNumber = int(mySqlSettingsDict["port_number"])
        self.username = mySqlSettingsDict["username"]
        self.password = mySqlSettingsDict["password"]
        self.database = mySqlSettingsDict["database"]
        self.connection = None  

    def getConnectionState(self):
        return self.__connectionState

    def establishConnection(self):
        try:
            logger.debug("Trying to connect to database:")
            logger.debug(f"HOST={self.hostAddress}:{self.portNumber}, USER={self.username}, DB={self.database}")
            self.connection = pymysql.connect(user=self.username, password=self.password,
                                    host=self.hostAddress, port=self.portNumber,
                                    database=self.database, 
                                    read_timeout=1, write_timeout=1, connect_timeout=1)
            self.dictCursor = self.connection.cursor(pymysql.cursors.DictCursor)
            self.__connectionState = "up"
            logger.info("Connection to database established.")
            return True
        except Exception as err:
            logger.error("Cannot connect to database!")
            logger.error(err)
            self.__connectionState= "down"
            return False
        
    def closeConnection(self):
        logger.info("Connection to database closed.")
        try:
            self.connection.close()
        except:
            logging.warning("Connection to database could not be closed! Ignoring!")
            pass

    """
    Checks whether there is a working database connection 
    and reestablishes when there isn't.

    Args: 
        None
    Returns:
        connectionState: The connection state to the MySql server
        connectionStateChanged: This indicates, whether the connection
            state is now different to the one specified in 
            __connectionState.
            This information is used by the GUI to update the layout.
    """
    def ensureDatabaseConnection(self):
        lastConnectionState = self.__connectionState
        if self.connection == None:
            # Here we land only when the application has just been started and a database connection has not yet been established.
            # This is the regular way for connection to be established for the first time.
            self.establishConnection()
        else:
            try:
                self.connection.ping(reconnect=True)
                self.__connectionState = "up"
            except:
                self.__connectionState = "down"

        if not self.__connectionState == lastConnectionState:
            connectionStateChanged = True
        else:
            connectionStateChanged = False

        return self.__connectionState, connectionStateChanged

    def insertDataset(self, dataset):
        insertPurchase = (
            "INSERT INTO udp_data (product_id, user_id, price_then, price_factor_then) VALUES (%s, %s, %s, %s)"
        )
        try:
            logger.debug(self.dictCursor.mogrify(insertPurchase, ( product.id, user.id, product.price, user.price_factor) ))
            self.dictCursor.execute(insertPurchase, ( product.id, user.id, product.price, user.price_factor) )
            return True
        except Exception as err:
            self.connection.rollback()
            logger.error("Failed to insert purchase into database:")
            logger.error(err)
            return False
