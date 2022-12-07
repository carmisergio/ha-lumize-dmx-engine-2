# Lumize DMX Engine 2 interface
#
# Module to communicate with the Lumize DMX Engine 2

from .tcp import TcpConnection, NotConnected  # TcpConnection class


class SendError(Exception):
    pass


class WrongChannel(Exception):
    pass


class LumizeDMXEngine2Light:
    def __init__(self, connection: TcpConnection, channel: int):
        self.__connection = connection
        self.__channel = channel

    async def turn_on(self, brightness: int = None, transition: int = None):
        print(f"[LIGHT {self.__channel}] Turning ON...")

        # Construct message
        message: str = f"on,{self.__channel}"
        if brightness is not None:
            message += f",b{brightness}"
        if transition is not None:
            message += f",t{transition*1000}"

        # Send message
        try:
            response = await self.__connection.request(message)
            print(response)
            if response.strip() != "ok":
                raise SendError
        except NotConnected:
            raise SendError

        return True

    async def turn_off(self, transition: int = None):
        print(f"[LIGHT {self.__channel}] Turning OFF...")

        # Construct message
        message: str = f"off,{self.__channel}"
        if transition is not None:
            message += f",t{transition*1000}"

        # Send message
        try:
            response = await self.__connection.request(message)
            if response.strip() != "ok":
                raise SendError
        except NotConnected:
            raise SendError

        return True

    async def get_state(self):
        print(f"[LIGHT {self.__channel}] Getting state...")

        # Construct message
        message: str = f"sreq,{self.__channel}"

        print(message)

        # Send message
        try:
            response = await self.__connection.request(message)
            print(response)

            response_split = response.strip().split(",")

            if response_split[0] != "sres":
                print("Wrong return message")
                raise SendError

            if int(response_split[1]) != self.__channel:
                print(
                    f"Response channel: {response_split[1]}, expected channel: {self.__channel}"
                )
                print(type(self.__channel))
                raise SendError

            state_split = response_split[2].split("-")

            return (bool(int(state_split[0])), int(state_split[1]))

        except NotConnected:
            raise SendError

        return True

    def is_available(self):
        """See if the light is available"""
        return self.__connection.is_ok()


class LumizeDMXEngine2:
    # TODO REMOVE LOGGER INFO
    def __init__(self, host: str, port: int, logger_info):
        logger_info("Init Lumize DMX Engine 2!")
        self.__connection = TcpConnection(host, port, logger_info, True)

    def start(self) -> None:
        self.__connection.start()

    def stop(self) -> None:
        self.__connection.stop()

    def get_light_entity(self, channel: int) -> LumizeDMXEngine2Light:

        # See if channel is in range
        if channel < 0 or channel >= 512:
            raise WrongChannel
        return LumizeDMXEngine2Light(self.__connection, channel)


# Check if module is being run as program
if __name__ == "__main__":
    print("This is a module and it should not be run as program.")
