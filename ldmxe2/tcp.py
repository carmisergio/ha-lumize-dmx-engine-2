import socket
import threading
import multiprocessing
import asyncio

WELCOME_MESSAGE = b"Lumize DMX Engine v2.0\n"
CONNECTION_CHECK_INTERVAL: int = 10
CONNECTION_CHECK_MESSAGE: str = "conncheck"
CONNECTION_CHECK_EXPECTED_RESPONSE: str = "ok"

LOG_DEBUG_DEFAULT = True

# Exception types
class ReconnectError(Exception):
    pass


class NotConnected(Exception):
    pass


class TcpConnection:
    """Class that represents a TCP connection to the Lumize DMX Engine"""

    def __init__(
        self, host: str, port: int, logger_info, log_debug: bool = LOG_DEBUG_DEFAULT
    ) -> None:
        self.__host: str = host
        self.__port: int = port
        self.__log_debug: bool = log_debug
        self.__logger_info = logger_info

        self.__running: bool = True
        self.__is_connected: bool = False

        # Start connection checker thread
        self.__connection_checker_cv = multiprocessing.Condition()
        self.__connection_checker_thread = threading.Thread(
            target=self.__check_connection
        )
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket_lock = threading.Lock()

    def start(self) -> None:
        """Starts the connection"""
        try:
            self.__reconnect()
        except ReconnectError:
            if self.__log_debug:
                self.__logger_info("[TCP] First connection unsuccesful")

        # self.__connection_checker_thread.start()

    def stop(self) -> None:
        """Stops the connection"""
        self.__running = False

        # Notify connection checker that we want to exit immediately
        with self.__connection_checker_cv:
            self.__connection_checker_cv.notify()

        # Wait for conneciton checker thread to finish execution
        self.__logger_info("Wait for thread")
        self.__connection_checker_thread.join()
        self.__logger_info("Thread awaited for thread")

        if self.__log_debug:
            self.__logger_info("[TCP] Closing connection...")

        # Close socket
        try:
            self.__socket.close()
        except socket.error:
            pass

    def is_ok(self) -> bool:
        """Is the connection ok"""
        return self.__is_connected

    def __reconnect(self):
        if self.__log_debug:
            self.__logger_info(
                f"[TCP] Attepting connection to {self.__host}, port: {self.__port}"
            )

        # Lock socket mutex
        with self.__socket_lock:
            try:
                print("[LUMIZE TCP] __reconnect: got socket lock")
                # Create socket
                self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Connect to address
                self.__socket.connect((self.__host, self.__port))

                # Read welcome message
                self.__socket.settimeout(5)  # Set timeout to receive welcome message
                received_message: bytes = self.__socket.recv(len(WELCOME_MESSAGE) + 5)
                print(f"[LUMIZE TCP] __reconnect: received message: {received_message}")

            except socket.error as error:
                if self.__log_debug:
                    self.__logger_info(f"[TCP] Socket error while connecting: {error}")
                    self.__logger_info(error)

                self.__socket.close()
                self.__is_connected = False
                raise ReconnectError

            # Check that remote host responded correctly
            if received_message == WELCOME_MESSAGE:
                if self.__log_debug:
                    self.__logger_info("[TCP] Connected!")

                self.__is_connected = True
                # self.__socket.settimeout(None)
            else:
                if self.__log_debug:
                    self.__logger_info(
                        "[TCP] Remote host didn't respond correctly, disconnecting."
                    )
                self.__socket.close()
                self.__is_connected = False
                raise ReconnectError

    def __check_connection(self) -> None:
        while self.__running:
            if self.__log_debug:
                self.__logger_info("[TCP], Checking connection...")

            self.__logger_info("Checking")
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
            with self.__connection_checker_cv:
                self.__connection_checker_cv.wait(timeout=CONNECTION_CHECK_INTERVAL)

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
                except socket.error:
                    raise NotConnected
            except ReconnectError:
                raise NotConnected


# Check if module is being run as program
if __name__ == "__main__":
    print("This is a module and it should not be run as program.")
