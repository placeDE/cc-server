import json
import random
import re
import time
from io import BytesIO

import aiohttp
import websockets
from PIL import Image

from application.color import get_matching_color, Color, get_color_from_index
from application.static_stuff import CANVAS_UPDATE_INTERVAL
from application.target_configuration.target_configuration import TargetConfiguration

BOARD_SIZE_X = 2000
BOARD_SIZE_Y = 2000


class Canvas:
    def __init__(self, target_configuration: TargetConfiguration):
        self.access_token = ""
        self.last_update = 0
        self.colors = []  # 2D array of the entire board (BOARD_SIZE_X x BOARD_SIZE_Y), Color objects
        self.target_configuration: TargetConfiguration = target_configuration
        self.mismatched_pixels = []

        # Fill with white preset
        for x in range(BOARD_SIZE_X):
            column = []
            for y in range(BOARD_SIZE_Y):
                column.append(Color.WHITE)
            self.colors.append(column)

    async def update_image(self, raw_image, offset_x, offset_y):
        self.last_update = time.time()

        image = Image.open(raw_image)
        image_data = image.convert("RGB").load()

        # convert to color indices
        for y in range(image.height):
            for x in range(image.width):
                self.colors[x + offset_x][y + offset_y] = get_matching_color(image_data[x, y])

        print("Board updated.")

    def get_pixel_color(self, x: int, y: int) -> Color:
        return self.colors[x][y]

    async def calculate_mismatched_pixels(self):
        mismatched_pixels = []
        for target_pixel in await self.target_configuration.get_pixels():
            current_color = self.get_pixel_color(target_pixel["x"], target_pixel["y"])
            if current_color is None:
                print("Couldn't determine color for pixel at " + str(target_pixel["x"]) + ", " + str(target_pixel["y"]))
                continue

            if current_color is None \
                    or current_color.value["id"] != target_pixel["color_index"] \
                    and get_color_from_index(target_pixel["color_index"]):
                mismatched_pixels.append(target_pixel)

        if len(mismatched_pixels) == 0:
            return []

        for p in mismatched_pixels:
            if p.get("priority") is None:
                print(p)
                continue
            p.update({"priority": [p["priority"][0], p["priority"][1] * random.randint(0, 100) / 100]})

        self.mismatched_pixels = list(sorted(mismatched_pixels, key=lambda x: x["priority"]))

    async def pop_mismatched_pixel(self):
        if len(self.mismatched_pixels) > 0:
            return self.mismatched_pixels.pop(0)
        return False

    async def update_access_token(self):
        """
        Fetch a valid AccessToken
        """

        print("Obtaining AccessToken token...")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://new.reddit.com/r/place/") as resp:
                if resp.status != 200:
                    print("No token!")
                    return

                if access_token_sequence := re.search(r"\"accessToken\":\"([\w0-9_\-]*)\"", await resp.text()):
                    self.access_token = access_token_sequence.group(1)
                    print("AccessToken: " + self.access_token)
                else:
                    print("No token!")

    async def update_board(self):
        """
        Fetch the current state of the board/canvas for the requed areas
        """
        if self.last_update + CANVAS_UPDATE_INTERVAL >= time.time():
            return False

        await self.update_access_token()

        results = []

        if (to_update := (await self.target_configuration.get_config()).get(
                "canvases_enabled")) is None:  # the configuration can disable some canvases to reduce load
            # by default, use all (2 at the moment)
            to_update = [0, 1, 2, 3]

        for canvas_id in to_update:
            await self.update_canvas(canvas_id, results)

        for r in results:
            # Tell the board to update with the offset of the current canvas
            await self.update_image(*r)

        return True

    async def update_canvas(self, canvas_id, lst):
        """
        Connects a websocket and sends a request to the server for the current state of the board
        Uses the returned URL to request the actual image using HTTP
        :param canvas_id: the canvas to fetch
        """
        print("Getting board")
        try:
            # https://websocket-client.readthedocs.io/en/latest/core.html#websocket._core.create_connection

            async with websockets.connect("wss://gql-realtime-2.reddit.com/query", extra_headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0",
                "Origin": "https://hot-potato.reddit.com"
            }) as ws:
                await ws.send(
                    json.dumps(
                        {"type": "connection_init", "payload": {"Authorization": "Bearer " + self.access_token}}))
                await ws.recv()
                await ws.send(json.dumps(
                    {
                        "id": "2",
                        "type": "start",
                        "payload": {
                            "variables": {
                                "input": {
                                    "channel": {
                                        "teamOwner": "AFD2022",
                                        "category": "CANVAS",
                                        "tag": str(canvas_id),
                                    }
                                }
                            },
                            "extensions": {},
                            "operationName": "replace",
                            "query": "subscription replace($input: SubscribeInput!) {\n  subscribe(input: $input) {\n    id\n    ... on BasicMessage {\n      data {\n        __typename\n        ... on FullFrameMessageData {\n          __typename\n          name\n          timestamp\n        }\n        ... on DiffFrameMessageData {\n          __typename\n          name\n          currentTimestamp\n          previousTimestamp\n        }\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
                        },
                    }
                ))

                filename = ""
                while True:
                    temp = json.loads(await ws.recv())
                    if temp["type"] == "data":
                        msg = temp["payload"]["data"]["subscribe"]
                        if msg["data"]["__typename"] == "FullFrameMessageData":
                            filename = msg["data"]["name"]

                            print("Got image for canvas " + str(canvas_id) + ": " + filename)
                            async with aiohttp.ClientSession() as session:
                                async with session.get(filename) as resp:
                                    if resp.status == 200:
                                        img = BytesIO(await resp.content.read())

                                        # Tell the board to update with the offset of the current canvas
                                        if canvas_id == 0:
                                            x = 0
                                            y = 0
                                        if canvas_id == 1:
                                            x = 1000
                                            y = 0
                                        if canvas_id == 2:
                                            x = 0
                                            y = 1000
                                        if canvas_id == 3:
                                            x = 1000
                                            y = 1000
                                        lst.append((img, x, y))
                            break

        except Exception as e:  # reddit closes the connection sometimes
            print(e)
