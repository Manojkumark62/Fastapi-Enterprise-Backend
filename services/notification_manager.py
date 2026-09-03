from collections import defaultdict

from fastapi import WebSocket


class NotificationConnectionManager:
    """Tracks authenticated notification sockets for this application process."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def broadcast(self, user_id: int, message: dict) -> None:
        stale: list[WebSocket] = []
        for websocket in self._connections.get(user_id, set()).copy():
            try:
                await websocket.send_json(message)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(user_id, websocket)


notification_manager = NotificationConnectionManager()
