# library imports

from __future__ import annotations

import asyncio

# our imports
from application.target_configuration.target_configuration import TargetConfiguration
from application.canvas import canvas
from application.connections import websocket_server

# from fastapi import



# create target_configuration
target_configuration = TargetConfiguration()
# manage r/place canvas
monalisa = canvas.Canvas(target_configuration)
# server for remote bot connections
server = websocket_server.Server(monalisa, target_configuration.versions, {"host": "0.0.0.0", "port": 8080})

async def main_loop():
    while True:
        # update board if it needs to be updated
        if await monalisa.update_board():
            await monalisa.calculate_mismatched_pixels()
        await asyncio.sleep(30)


looper = asyncio.new_event_loop()
looper.create_task(main_loop())
looper.create_task(server.run(looper))
try:
    looper.run_forever()
except (KeyboardInterrupt, RuntimeError):
    print("Exiting!")
