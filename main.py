import asyncio
import json
from functools import lru_cache

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse

from application.api.commands import request_pixel, ping
from application.api.connection_manager import ConnectionManager
from application.api.config import ServerConfig
from application.canvas.canvas import Canvas
from application.target_configuration.target_configuration import TargetConfiguration

app = FastAPI()
connection_manager = ConnectionManager()


config = ServerConfig()
canvas: Canvas


async def update_canvas(monalisa: Canvas):
    if await monalisa.update_board():
        await monalisa.calculate_mismatched_pixels()
    await asyncio.sleep(30)


@app.on_event('startup')
async def startup():
    global canvas
    target_config = TargetConfiguration(config)
    canvas = Canvas(target_config)
    print('Scheduling canvas update')
    asyncio.create_task(update_canvas(canvas))


@app.websocket('/live')
async def live_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            print(f'RX: {json.dumps(data)}')
            if 'operation' in data:
                op = data['operation']
                response = None

                if op == 'request-pixel':
                    response = format_response(
                        'place-pixel',
                        data.get('user', ''),
                        await request_pixel(canvas)
                    )
                elif op == 'handshake':
                    metadata = data.get('data', {})
                    advertised_count = metadata.get('useraccounts', 1)
                    connection_manager.set_advertised_accounts(websocket, advertised_count)
                elif op == 'ping':
                    response = ping()

                if response is not None:
                    print(f'TX: {json.dumps(response)}')
                    await websocket.send_json(response)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


@app.get('/users/count')
async def get_users_count():
    return JSONResponse(content={
        'count': connection_manager.connection_count(),
        'advertised_accounts': connection_manager.advertised_account_count()
    })


def format_response(op: str, user: str, data: dict):
    return {
        'operation': op,
        'data': data,
        'user': user
    }
