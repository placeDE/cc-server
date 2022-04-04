from typing import List

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.advertised_accounts: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def set_advertised_accounts(self, websocket: WebSocket, count):
        self.advertised_accounts[websocket] = count

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        self.advertised_accounts.pop(websocket)

    async def send_message_to(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    def connection_count(self):
        return len(self.active_connections)

    def advertised_account_count(self):
        print(self.advertised_accounts)
        return sum(self.advertised_accounts.values())
