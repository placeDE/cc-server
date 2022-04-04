from application.api.config import ServerConfig
from application.canvas.canvas import Canvas
from application.color import get_color_from_index


async def request_pixel(canvas: Canvas):
    pixel = await canvas.pop_mismatched_pixel()
    if pixel:
        return {
            'x': pixel['x'],
            'y': pixel['y'],
            'color': get_color_from_index(pixel['color_index']).value['id']
        }
    else:
        return {}


# no-op
async def handshake():
    pass


def ping():
    return {
        'pong': True
    }


def version_check(settings: ServerConfig, data: dict):
    client_version = data.get('version', -1)
    # wenn der client nix schickt nehmen wir an, dass er in ordnung ist
    return client_version < 0 or client_version < settings.min_version
