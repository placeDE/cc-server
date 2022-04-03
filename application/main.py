# library imports

from __future__ import annotations

import asyncio

# our imports
from application.target_configuration.target_configuration import TargetConfiguration

# from fastapi import


# create target_configuration
from canvas import canvas
from connections import websocket_server

target_configuration = TargetConfiguration()
# manage r/place canvas
monalisa = canvas.Canvas(target_configuration)
# server for remote bot connections
server = websocket_server.Server(monalisa, {"host": "0.0.0.0", "port": 8080})

looper = asyncio.get_event_loop()

server.run(looper)


# looper.create_task()

async def main_loop():
    while True:
        # update board if it needs to be updated
        if monalisa.update_board():
            monalisa.calculate_mismatched_pixels()
        await asyncio.sleep(10)


looper.create_task(main_loop())
looper.run_forever()
