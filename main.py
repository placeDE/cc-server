import asyncio
import hashlib
import json

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

from application.api.commands import request_pixel, ping
from application.api.config import ServerConfig
from application.api.connection_manager import ConnectionManager
from application.canvas.canvas import Canvas
from application.target_configuration.target_configuration import TargetConfiguration

app = FastAPI()
connection_manager = ConnectionManager()

config = ServerConfig()
canvas: Canvas
target_config: TargetConfiguration


async def update_canvas(monalisa: Canvas):
    while True:
        try:
            await monalisa.update_board()
            await asyncio.sleep(10)
        finally:
            print('There was an error updating the canvas.')


@app.on_event('startup')
async def startup():
    global canvas, target_config
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

                    client_version = data.get('version', -1)
                    client_protocol = data.get('protocol', '')
                    versions = (await target_config.get_config()).get("versions")
                    target_version = versions.get(client_protocol, -1)
                    advertised_count = min(0, metadata.get('useraccounts', 1))

                    # wenn der client nix schickt nehmen wir an, dass er in ordnung ist
                    if client_version < 0 or target_version < 0 or client_version >= target_version:
                        response = format_response(
                            'notify-update',
                            data.get('user', ''),
                            {
                                'version', target_version
                            }
                        )
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
