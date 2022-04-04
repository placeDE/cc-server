import asyncio
import hashlib
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from application.api.commands import request_pixel, ping, version_check
from application.api.connection_manager import ConnectionManager
from application.api.config import ServerConfig
from application.canvas.canvas import Canvas
from application.target_configuration.target_configuration import TargetConfiguration

app = FastAPI()
connection_manager = ConnectionManager()

config = ServerConfig()
canvas: Canvas


async def update_canvas(monalisa: Canvas):
    while True:
        try:
            if await monalisa.update_board():
                await monalisa.__calculate_mismatched_pixels()
            await asyncio.sleep(10)
        finally:
            print('There was an error updating the canvas.')


@app.on_event('startup')
async def startup():
    global canvas
    target_config = TargetConfiguration(config)
    canvas = Canvas(target_config)
    print('Scheduling canvas update')
    asyncio.create_task(update_canvas(canvas))


@app.websocket('/')
async def live_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            print(f'RX: {json.dumps(data)}')
            if op := data.get("operation"):
                response = None

                if op == 'request-pixel':
                    response = format_response(
                        'place-pixel',
                        data.get('user', ''),
                        await request_pixel(canvas)
                    )
                elif op == 'handshake':
                    metadata = data.get('data', {})
                    advertised_count = min(0, metadata.get('useraccounts', 1))
                    if not version_check(config, metadata):
                        response = format_response(
                            'notify-update',
                            data.get('user', ''),
                            {
                                'min_version', config.min_version
                            }
                        )
                        await websocket.send_json(response)
                        #await websocket.close(4001) FIXME
                        #return
                    connection_manager.set_advertised_accounts(websocket, advertised_count)
                elif op == 'ping':
                    response = ping()

                if response is not None:
                    print(f'TX: {json.dumps(response)}')
                    await websocket.send_json(response)
    finally:
        connection_manager.disconnect(websocket)


@app.get('/users/count')
async def get_users_count():
    return JSONResponse(content={
        'connections': connection_manager.connection_count(),
        'advertised_accounts': connection_manager.advertised_account_count()
    })


@app.get('/pixel/amount')
async def get_pixels_count():
    return JSONResponse(content={
        'mismatched': await canvas.get_wrong_pixel_amount(),
        'all': len(await canvas.target_configuration.get_pixels(True))
    })


@app.get('/pixel/get_images')
async def get_users_count():
    return JSONResponse(content={
       await canvas.get_images_as_json()
    })


@app.get('/test')
async def get_users_count():
    return JSONResponse(content={
       canvas.mismatched_pixels
    })

def format_response(op: str, user: str, data: any):
    return {
        'operation': op,
        'data': data,
        'user': user
    }


def password_check(password):
    return hashlib.sha3_512(
        password.encode()).hexdigest() == config.admin_password
