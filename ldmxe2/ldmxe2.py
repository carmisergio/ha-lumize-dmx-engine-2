"""Lumize DMX Engine 2 interface module for python"""

from types import FunctionType

from .tcp import TcpConnection, NotConnected  # TcpConnection class

KEEP_ALIVE_DEFAULT: int = 0  # seconds

# Exception types
class SendError(Exception):
    """Command send error"""


class WrongChannel(Exception):
    """Trying to get LumizeDMXEngine2Light object for channel that doesn't exist"""


class LumizeDMXEngine2Light:
    """Object that references specific channel on the Lumize DMX Engine 2"""

    def __init__(self, connection: TcpConnection, channel: int):
        self.__connection = connection
        self.__channel = channel

    async def turn_on(self, brightness: int = None, transition: int = None):
        """Turn on channel"""

        # Construct message
        message: str = f"on,{self.__channel}"
        if brightness is not None:
            message += f",b{brightness}"
        if transition is not None:
            message += f",t{transition*1000}"

        # Send message
        try:
            response = await self.__connection.request(message)

            # Check response
            if response.strip() != "ok":
                raise SendError

        except NotConnected as not_connected:
            raise SendError from not_connected

        return True

    async def turn_off(self, transition: int = None):
        """Turn off channel"""

        # Construct message
        message: str = f"off,{self.__channel}"
        if transition is not None:
            message += f",t{transition*1000}"

        # Send message
        try:
            response = await self.__connection.request(message)

            # Check response
            if response.strip() != "ok":
                raise SendError

        except NotConnected as not_connected:
            raise SendError from not_connected

        return True

    async def get_state(self):
        """Get channel state"""

        # Construct message
        message: str = f"sreq,{self.__channel}"

        # Send message
        try:
            response = await self.__connection.request(message)

            response_split = response.strip().split(",")

            # Check response is a status response message
            if response_split[0] != "sres":
                raise SendError

            # Check reported channel in response matches channel of light
            if int(response_split[1]) != self.__channel:
                raise SendError

            # Extract state from response
            state_split = response_split[2].split("-")
            state = bool(int(state_split[0]))
            brightness = int(state_split[1])

            return (state, brightness)

        except NotConnected as not_connected:
            raise SendError from not_connected

        return True

    def is_available(self):
        """Returns true if the connection to the engine is ok"""
        return self.__connection.is_ok()


class LumizeDMXEngine2:
    """Lumize DMX Engine 2 connection instance"""

    def __init__(
        self,
        host: str,
        port: int,
        ext_logger: FunctionType or None = None,
        keep_alive: int = KEEP_ALIVE_DEFAULT,
    ):

        # Setup print as logger if no external logger function is provided
        if ext_logger is None:
            self.__logger = print
        else:
            self.__logger = ext_logger

        self.__logger("Init Lumize DMX Engine 2!")

        # Setup connection
        self.__connection = TcpConnection(host, port, self.__logger, keep_alive)

    def start(self) -> None:
        """Start connection to the Lumize DMX Engine 2"""
        self.__connection.start()

    def stop(self) -> None:
        """Stop connection to the Lumize DMX Engine 2"""
        self.__connection.start()
        self.__connection.stop()

    def get_light_entity(self, channel: int) -> LumizeDMXEngine2Light:
        """Returns LumizeDMXEngine2Light object for given channel"""

        # See if channel is in range
        if channel < 0 or channel >= 512:
            raise WrongChannel

        return LumizeDMXEngine2Light(self.__connection, channel)


# Check if module is being run as program
if __name__ == "__main__":
    print("This is a module and it should not be run as program.")
