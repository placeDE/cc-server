from application.canvas.canvas import Canvas
from application.color import get_color_from_index


async def get_pixel_data(pixel: dict):
    return {
        'x': pixel['x'],
        'y': pixel['y'],
        'color': get_color_from_index(pixel['color_index']).value['id']
    }


# no-op
async def handshake():
    pass


def ping():
    return {
        'pong': True
    }
