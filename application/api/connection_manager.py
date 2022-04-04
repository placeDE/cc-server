from typing import List, Tuple

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[Tuple[WebSocket, str]] = []
        self.advertised_accounts: dict = {}

    async def connect(self, uuid: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append((websocket, uuid))

    def set_advertised_accounts(self, uuid: str, count):
        self.advertised_accounts[uuid] = count

    def disconnect(self, uuid: str, websocket: WebSocket):
        self.active_connections.remove((websocket, uuid))
        self.advertised_accounts.pop(uuid)

    async def send_message_to(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection[0].send_text(message)

    def connection_count(self):
        return len(self.active_connections)

    def advertised_account_count(self):
        return sum(self.advertised_accounts.values())
