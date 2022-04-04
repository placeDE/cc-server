import asyncio
from functools import lru_cache

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from application.api.commands import request_pixel, handshake, ping
from application.canvas.canvas import Canvas
from application.target_configuration.target_configuration import TargetConfiguration
from connection_manager import ConnectionManager
from config import ServerConfig

app = FastAPI()
connection_manager = ConnectionManager()


@lru_cache
def get_config():
    return ServerConfig()


async def update_canvas(monalisa: Canvas):
    if await monalisa.update_board():
        await monalisa.calculate_mismatched_pixels()
    await asyncio.sleep(30)


canvas: Canvas


@app.on_event('startup')
async def startup(background_tasks: BackgroundTasks, config: ServerConfig = Depends(get_config)):
    global canvas

    target_config = TargetConfiguration(config)
    canvas = Canvas(target_config)

    background_tasks.add_task(update_canvas, canvas)


@app.websocket('/live')
async def live_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
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
                    pass
                elif op == 'ping':
                    response = ping()

                if response is not None:
                    await websocket.send_json(response)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


@app.get('/users/count')
async def get_users_count():
    return JSONResponse(content={
        'count': connection_manager.connection_count()
    })


def format_response(op: str, user: str, data: dict):
    return {
        'operation': op,
        'data': data,
        'user': user
    }
