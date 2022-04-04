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


# no-op
async def handshake():
    pass


async def ping():
    return {
        'pong': True
    }
