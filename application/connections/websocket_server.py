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
        bot_count = 0

        try:
            # TODO: check for update availability.

            async for msg in socket:
                req = json.loads(msg)

                if req.get("operation") == "request-pixel":
                    print(msg)
                    pixel = await self.provider.pop_mismatched_pixel()
                    if pixel:
                        data = {
                            "x": pixel["x"],
                            "y": pixel["y"],
                            "color": get_color_from_index(pixel["color_index"]).value["id"]
                        }

                        await socket.send(json.dumps(Server.__wrap_data(data, req.get("user", ""))))
                    else:
                        await socket.send("null")

                elif req.get("operation") == "handshake":
                    bot_count = req["data"].get("useraccounts", 1)
                    if bot_count < 0 or bot_count > 100:
                      print(f"Ignoring illegal connection: A client pretends to have {bot_count} bots.")
                      bot_count = 0
                    else:
                      self.__client_count += bot_count
                      print(f"{bot_count} New Client(s) connected! New bot count: {self.__client_count}")

                elif req.get("operation") == "get-botcount":
                    await socket.send(json.dumps({"amount": self.__client_count}))

                elif req.get("operation") == "ping":
                    await socket.send(json.dumps({"pong": True}))

        except websockets.ConnectionClosed:
            pass
        finally:
            self.__client_count -= bot_count
            print(f"{bot_count} Client(s) lost! New bot count: {self.__client_count}")

    @staticmethod
    def __wrap_data(data: dict, user: str, operation: str = "place-pixel") -> dict:
        return {
                "operation": operation,
                "data": data,
                "user": user
            }

    def get_bot_count(self) -> int:
        return self.__client_count
