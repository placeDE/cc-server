import asyncio
import hashlib
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
versions: dict

async def update_canvas(monalisa: Canvas):
    while True:
        try:
            if await monalisa.update_board():
                await monalisa.calculate_mismatched_pixels()
            await asyncio.sleep(30)
        finally:
            print('There was an error updating the canvas.')


@app.on_event('startup')
async def startup():
    global canvas
    global versions
    target_config = TargetConfiguration(config)
    versions = target_config.versions
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

                    client_version = data.get('version', -1)
                    client_protocol = data.get('protocol', '')
                    target_version = versions.get(client_protocol, -1)

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
                # eigtl. durch /users/count deprecated
                elif op == 'get-botcount' and password_check(data.get("pw", '')):
                    response = {'amount': connection_manager.advertised_account_count()}

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


def format_response(op: str, user: str, data: any):
    return {
        'operation': op,
        'data': data,
        'user': user
    }


def password_check(password):
    return hashlib.sha3_512(
        password.encode()).hexdigest() == "bea976c455d292fdd15256d3263cb2b70f051337f134b0fa9678d5eb206b4c45ebd213694af9cf6118700fc8488809be9195c7eae44a882c6be519ba09b68e47"
