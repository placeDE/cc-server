import asyncio
import json
from typing import Dict, Any

import websockets.server
from websockets import serve
from websockets.server import WebSocketServerProtocol

from application.color import get_color_from_index
from application.canvas.canvas import Canvas

DEFAULT_PORT = 5555
DEFAULT_HOST = "localhost"


class Server:
    """
    Websocket server, dieser managed die Verbindung zu den client Bots und teilt denen auf Anfrage neue Pixel zu.
    """
    __slots__ = ("config", "port", "__server_loop", "__server", "host", "provider", "__client_count")
    __client_count: int
    config: Dict[str, Any]
    port: int
    host: str
    provider: Canvas

    def __init__(self, provider: Canvas, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self.port = config.get("port", DEFAULT_PORT)
        self.host = config.get("host", DEFAULT_HOST)
        self.__server_loop = None
        self.__server = None
        self.__client_count = 0

    async def run(self, looper: asyncio.AbstractEventLoop):
        """
        erstellt den server und lässt diesen unendlich laufen. Sollte evtl. in einem eigenen Thread aufgerufen werden.
        """
        async with serve(self.__handler, self.host, self.port):
            while True:
                await asyncio.sleep(1000000)
            #await asyncio.Future()

    async def __handler(self, socket: WebSocketServerProtocol):
        self.__client_count += 1
        print(f"New Client connected! New client count: {self.__client_count}")

        try:
            # TODO: check for update availability.

            async for msg in socket:
                if msg == "request_pixel":
                    pixel = await self.provider.pop_mismatched_pixel()
                    if pixel:

                        pixel.update({"colour": get_color_from_index(pixel["color_index"])})
                        del pixel["priority"]

                        await socket.send(json.dumps(Server.__wrap_data(pixel)))
                    else:
                        await socket.send("null")
        except websockets.ConnectionClosed:
            pass
        finally:
            self.__client_count -= 1

    @staticmethod
    async def __wrap_data(data: dict, operation: str = "pixel") -> dict:
        return {
                "operation": operation,
                "data": data
            }

    def get_connection_count(self) -> int:
        return self.__client_count
