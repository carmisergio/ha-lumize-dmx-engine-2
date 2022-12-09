"""Lumize DMX Engine 2 TCP connection handling module"""
import socket
import threading
import multiprocessing
import asyncio

from types import FunctionType

# Configuration constants
WELCOME_MESSAGE = b"Lumize DMX Engine v2.0\n"
CONNECTION_CHECK_EXPECTED_RESPONSE: str = "ok"
CONNECTION_CHECK_MESSAGE: str = "conncheck"

# Exception types
class ReconnectError(Exception):
    """Error in reconnecting to Lumize DMX Engine 2"""


class NotConnected(Exception):
    """Tried sending command but connection to Lumize DMX Engine 2 can't be enstablished"""


class TcpConnection:
    """Class that represents a TCP connection to the Lumize DMX Engine 2"""

    def __init__(
        self,
        host: str,
        port: int,
        ext_logger: FunctionType,
        keep_alive: int,
    ) -> None:
        self.__host: str = host
        self.__port: int = port
        self.__keep_alive_interval = keep_alive
        self.__run_keep_alive = keep_alive > 0  # If keep_alive is 0s, don't run

        # Setup print as logger if no external logger function is provided
        if ext_logger is None:
            self.__logger = print
        else:
            self.__logger = ext_logger

        # Setup state variables
        self.__running: bool = True
        self.__is_connected: bool = False

        self.__keep_alive_cv = multiprocessing.Condition()
        self.__keep_alive_thread = threading.Thread(target=self.__keep_alive)

        # Init socket and respective lock
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket_lock = threading.Lock()

    def start(self) -> None:
        """Starts the connection"""
        try:
            self.__reconnect()
        except ReconnectError:
            self.__logger("[TCP] First connection unsuccesful")

        # Start keep alive thread if configured
        if self.__run_keep_alive:
            self.__keep_alive_thread.start()

    def stop(self) -> None:
        """Stops the connection"""
        self.__running = False

        if self.__run_keep_alive:
            # Notify connection checker that we want to exit immediately
            with self.__keep_alive_cv:
                self.__keep_alive_cv.notify()

            # Wait for conneciton checker thread to finish execution
            self.__keep_alive_thread.join()

        self.__logger("[TCP] Closing connection...")

        # Close socket
        try:
            self.__socket.close()
        except socket.error:
            pass

    def is_ok(self) -> bool:
        """Is the connection ok"""
        return self.__is_connected

    def __reconnect(self):
        self.__logger(
            f"[TCP] Attepting connection to {self.__host}, port: {self.__port}"
        )

        # Lock socket mutex
        with self.__socket_lock:
            try:
                # Create socket
                self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Connect to address
                self.__socket.connect((self.__host, self.__port))

                # Read welcome message
                self.__socket.settimeout(5)  # Set timeout to receive welcome message
                received_message: bytes = self.__socket.recv(len(WELCOME_MESSAGE) + 5)

            except socket.error as error:
                self.__logger(f"[TCP] Socket error while connecting: {error}")
                self.__logger(error)

                self.__socket.close()
                self.__is_connected = False
                raise ReconnectError from error

            # Check that remote host responded correctly
            if received_message == WELCOME_MESSAGE:
                self.__logger("[TCP] Connected!")

                self.__is_connected = True
                # self.__socket.settimeout(None)
            else:
                self.__logger(
                    "[TCP] Remote host didn't respond correctly, disconnecting."
                )
                self.__socket.close()
                self.__is_connected = False
                raise ReconnectError

    def __keep_alive(self) -> None:
        while self.__running:
            self.__logger("[TCP], Checking connection...")

            # Send connection check command
            try:
                conncheck_response: str = asyncio.run(
                    self.request(CONNECTION_CHECK_MESSAGE)
                )
                if conncheck_response != CONNECTION_CHECK_EXPECTED_RESPONSE:
                    try:
                        self.__reconnect()
                    except ReconnectError:
                        pass
            except NotConnected:
                try:
                    self.__reconnect()
                except ReconnectError:
                    pass

            # Wait for connection check interval or or notification from other thread
            with self.__keep_alive_cv:
                self.__keep_alive_cv.wait(timeout=self.__keep_alive_interval)

    async def request(self, request_msg: str) -> str:
        """Sends a request to the Lumize DMX Engine and retuns its response"""

        # Try to send message
        try:
            # First try
            with self.__socket_lock:
                self.__socket.sendall(bytes(request_msg, "utf-8"))
                response_msg: bytes = self.__socket.recv(64)
                return response_msg.decode("utf-8").strip()
        except socket.error:
            try:
                self.__reconnect()
                try:
                    # Second try after reconnect
                    with self.__socket_lock:
                        self.__socket.sendall(bytes(request_msg, "utf-8"))
                        response_msg: bytes = self.__socket.recv(64)
                        return response_msg.decode("utf-8").strip()
                except socket.error as error:
                    raise NotConnected from error
            except ReconnectError as error:
                raise NotConnected from error


# Check if module is being run as program
if __name__ == "__main__":
    print("This is a module and it should not be run as program.")
