import json
import random
import time

import aiohttp

from application import static_stuff
from application.api.config import ServerConfig

UPDATE_INTERVAL = 60


class TargetConfiguration:
    """
    Represents the target configuration containing the template / pixels to be drawn
    Is refreshed periodically by pulling it from a server
    """

    def __init__(self, settings: ServerConfig):
        self.last_update = 0
        self.config = {}
        self.pixels = []
        self.settings = settings
        print(settings)

    async def get_config(self, ignore_time: bool = False):
        """
        Get the config and refresh it first if necessary
        """
        if self.last_update + self.settings.canvas_update_interval < time.time() and not ignore_time:
            await self.refresh_config()
            self.last_update = time.time()

            lst = []
            priorities = self.config["priorities"]
            for s in self.config["structures"].values():
                prio = (priorities.get(str(s.get("priority"))) or 0) * random.randint(0, 100) / 100
                for p in s.get("pixels"):
                    lst.append({"x": p["x"], "y": p["y"], "color_index": p["color"],
                                "priority": [prio, priorities.get(str(p.get("priority"))) or 0]})
            self.pixels = lst

        return self.config

    async def refresh_config(self):
        """
        Pulls the config from the server configured in config.json or falls back to reading a local file if specified as such
        """
        print("\nRefreshing target configuration...\n")

        url = self.settings.remote_config_url

        if url.startswith("http"):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    json_data = await resp.json()
                    if resp.status != 200:
                        print("Error: Could not get config file from " + static_stuff.target_configuration_url)
                        return

                    # parse config file
                    self.config = json_data
        else:
            # not a remote url, fallback to local file
            with open(url, "r") as f:
                self.config = json.load(f)

    async def get_pixels(self):
        await self.get_config()
        return self.pixels
