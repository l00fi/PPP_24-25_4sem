import websockets
import asyncio
import json

from app.core.config import Settings

async def websocket_client():
    # Подключение к WebSocket-серверу
    async with websockets.connect(f"ws://{Settings.IP}:{Settings.PORT}/ws/1") as ws: # notifications
        print("Подключено к серверу. Введите 'exit' для выхода.")
        
        try:
            while True:
                # Ввод task_id вручную
                task_id = input("Введите task_id (или 'exit'): ").strip()
                if task_id.lower() == "exit":
                    break
                
                # Отправка task_id на сервер
                await ws.send(json.dumps({"task_id": task_id}))
                
                # Ожидание уведомлений
                while True:
                    message = await ws.recv()
                    print(f"Уведомление по задаче {task_id}: {message}")

        except websockets.exceptions.ConnectionClosed:
            print("Соединение закрыто сервером.")

if __name__ == "__main__":
    asyncio.run(websocket_client())