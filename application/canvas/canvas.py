import json
import random
import re
import time
from io import BytesIO
from threading import Thread
from typing import TYPE_CHECKING

import requests
from PIL import Image
from websocket import create_connection

from application.color import get_matching_color, Color, get_color_from_index
from application.static_stuff import CANVAS_UPDATE_INTERVAL, GRAPHQL_GET_CONFIG, get_graphql_canvas_query

from application.target_configuration.target_configuration import TargetConfiguration

BOARD_SIZE_X = 2000
BOARD_SIZE_Y = 1000


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
        self.update_board()

    def update_image(self, raw_image, offset_x, offset_y):
        self.last_update = time.time()

        image = Image.open(raw_image)
        image_data = image.convert("RGB").load()

        # convert to color indices
        for x in range(image.width):
            for y in range(image.height):
                self.colors[x + offset_x][y + offset_y] = get_matching_color(image_data[x, y])

        print("Board updated.")

    def get_pixel_color(self, x: int, y: int) -> Color:
        return self.colors[x][y]

    def calculate_mismatched_pixels(self):
        mismatched_pixels = []
        for target_pixel in self.target_configuration.get_pixels():
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
            p.update({"priority": [p["priority"][0], p["priority"][1] * random.randint(0, 100) / 100]})

        self.mismatched_pixels = list(sorted(mismatched_pixels, key=lambda x: x["priority"]))

    def pop_mismatched_pixel(self):
        if len(self.mismatched_pixels) > 0:
            return self.mismatched_pixels.pop(0)
        return False

    def update_access_token(self):
        """
        Fetch a valid AccessToken
        """

        print("Obtaining AccessToken token...")
        r = requests.get("https://new.reddit.com/r/place/")
        time.sleep(1)

        access_token_sequence = re.search(r"\"accessToken\":\"(\"[^\"]*)\"", r.text)
        self.access_token = access_token_sequence[15:][:-1]
        print("AccessToken: " + self.access_token)
        time.sleep(1)

    def update_board(self):
        """
        Fetch the current state of the board/canvas for the requed areas
        """
        if self.last_update + CANVAS_UPDATE_INTERVAL >= time.time():
            return False

        self.update_access_token()

        results = []
        threads = []

        if "canvases_enabled" in self.target_configuration.get_config():  # the configuration can disable some canvases to reduce load
            to_update = self.target_configuration.get_config()["canvases_enabled"]
        else:  # by default, use all (2 at the moment)
            to_update = [0, 1]

        for canvas_id in to_update:
            t = Thread(target=self.update_canvas, args=[canvas_id, results], daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        for r in results:
            # Tell the board to update with the offset of the current canvas
            self.update_image(*r)

        return True

    def update_canvas(self, canvas_id, lst):
        """
        Connects a websocket and sends a request to the server for the current state of the board
        Uses the returned URL to request the actual image using HTTP
        :param canvas_id: the canvas to fetch
        """
        print("Getting board")
        try:
            ws = create_connection("wss://gql-realtime-2.reddit.com/query")
            ws.send(
                json.dumps({"type": "connection_init", "payload": {"Authorization": "Bearer " + self.access_token}, }))
            ws.recv()
            ws.send(json.dumps(GRAPHQL_GET_CONFIG))
            ws.recv()
            ws.send(get_graphql_canvas_query(canvas_id))

            filename = ""
            while True:
                temp = json.loads(ws.recv())
                if temp["type"] == "data":
                    msg = temp["payload"]["data"]["subscribe"]
                    if msg["data"]["__typename"] == "FullFrameMessageData":
                        filename = msg["data"]["name"]

                        print("Got image for canvas " + str(canvas_id) + ": " + filename)
                        img = BytesIO(requests.get(filename, stream=True).content)
                        lst.append((img, 1000 * canvas_id, 0))
                        break

            ws.close()
        except:  # reddit closes the connection sometimes
            pass
