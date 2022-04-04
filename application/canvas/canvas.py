import asyncio
import base64
import json
import random
import re
import time
from io import BytesIO

import aiohttp
import websockets
from PIL import Image

from application.color import get_matching_color, Color, get_color_from_index, hex_to_rgba
from application.target_configuration.target_configuration import TargetConfiguration

BOARD_SIZE_X = 2000
BOARD_SIZE_Y = 2000


async def image_to_string(image: Image):
    if not image:
        return ""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


class Canvas:
    def __init__(self, target_configuration: TargetConfiguration):
        self.access_token = ""
        self.last_update = 0
        self.colors = []  # 2D array of the entire board (BOARD_SIZE_X x BOARD_SIZE_Y), Color objects
        self.mismatched_pixels = []
        self.mismatched_pixel_dict = {}
        self.lock = asyncio.Lock()
        self.target_configuration: TargetConfiguration = target_configuration
        self.correct_image = None
        self.wrong_pixel_image = None
        self.target_pixel_image = None

        # Fill with white preset
        for x in range(BOARD_SIZE_X):
            column = []
            for y in range(BOARD_SIZE_Y):
                column.append(Color.WHITE)
            self.colors.append(column)

    async def __update_image(self, raw_image, offset_x, offset_y):
        self.last_update = time.time()

        image = Image.open(raw_image)
        image_data = image.convert("RGB").load()

        # convert to color indices
        for y in range(image.height):
            for x in range(image.width):
                self.colors[x + offset_x][y + offset_y] = get_matching_color(image_data[x, y])

    def __get_pixel_color(self, x: int, y: int) -> Color:
        return self.colors[x][y]

    async def __calculate_mismatched_pixels(self):
        mismatched_pixels = []
        mismatched_pixel_dict = {}
        for target_pixel in await self.target_configuration.get_pixels():
            current_color = self.__get_pixel_color(target_pixel["x"], target_pixel["y"])
            if current_color is None:
                print("Couldn't determine color for pixel at " + str(target_pixel["x"]) + ", " + str(target_pixel["y"]))
                continue

            if current_color is None \
                    or current_color.value["id"] != target_pixel["color_index"] \
                    and get_color_from_index(target_pixel["color_index"]):
                mismatched_pixels.append(target_pixel)
                mismatched_pixel_dict.update({(target_pixel["x"], target_pixel["y"]): target_pixel})

        if len(mismatched_pixels) == 0:
            return []

        for p in mismatched_pixels:
            p.update({"priority": [p["priority"][0], p["priority"][1] * random.randint(0, 100) / 100]})

        self.mismatched_pixels = list(sorted(mismatched_pixels, key=lambda x: x["priority"]))
        self.mismatched_pixel_dict = mismatched_pixel_dict

    async def __update_access_token(self):
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
                else:
                    print("No token!")

    async def __update_canvas(self, canvas_id, lst):
        """
        Connects a websocket and sends a request to the server for the current state of the board
        Uses the returned URL to request the actual image using HTTP
        :param canvas_id: the canvas to fetch
        """
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

    async def __generate_images(self):
        print("image generation started")
        #correct_image = Image.new(mode="RGBA", size=(2000, 2000),
        #                              color=(0, 0, 0, 0))
        wrong_pixel_image = Image.new(mode="RGBA", size=(2000, 2000),
                                      color=(0, 0, 0, 0))
        target_pixel_image = Image.new(mode="RGBA", size=(2000, 2000),
                                       color=(0, 0, 0, 0))
        for x in range(2000):
            for y in range(2000):
                """if px := self.target_configuration.pixel_dict.get((x, y)):
                    correct_image.putpixel((x, y),
                                           hex_to_rgba(get_color_from_index(px['color_index']).value["hex"], False))
                else:
                    correct_image.putpixel((x, y), hex_to_rgba(self.colors[x][y].value["hex"], False))"""

                if px := self.target_configuration.pixel_dict.get((x, y)):
                    if (x, y) in self.mismatched_pixel_dict:
                        wrong_pixel_image.putpixel((x, y),
                                                   hex_to_rgba(get_color_from_index(px['color_index']).value["hex"],
                                                               False))
                    else:
                        wrong_pixel_image.putpixel((x, y),
                                                   hex_to_rgba(get_color_from_index(px['color_index']).value["hex"],
                                                               True))

                if px := self.target_configuration.pixel_dict.get((x, y)):
                    target_pixel_image.putpixel((x, y),
                                                hex_to_rgba(get_color_from_index(px['color_index']).value["hex"],
                                                            False))

        #self.correct_image = correct_image
        self.wrong_pixel_image = wrong_pixel_image
        self.target_pixel_image = target_pixel_image

        print("image generation finished")

    async def pop_mismatched_pixel(self):
        async with self.lock:
            if len(self.mismatched_pixels) > 0:
                return self.mismatched_pixels.pop(0)
            return False

    async def get_wrong_pixel_amount(self):
        return len(self.mismatched_pixels)

    async def get_images_as_json(self):
        return {
            'reddit': await image_to_string(self.correct_image),
            'wrong': await image_to_string(self.wrong_pixel_image),
            'config': await image_to_string(self.target_pixel_image)
        }

    async def update_board(self):
        """
        Fetch the current state of the board/canvas for the requed areas
        """
        if self.last_update + self.target_configuration.settings.canvas_update_interval >= time.time():
            return
        await self.__update_access_token()

        results = []

        if (to_update := (await self.target_configuration.get_config(True)).get(
                "canvases_enabled")) is None:  # the configuration can disable some canvases to reduce load
            # by default, use all (2 at the moment)
            to_update = [0, 1, 2, 3]

        for canvas_id in to_update:
            await self.__update_canvas(canvas_id, results)

        async with self.lock:
            for r in results:
                # Tell the board to update with the offset of the current canvas
                await self.__update_image(*r)

            print("Board updated!")

        await self.__calculate_mismatched_pixels()
        await self.__generate_images()
