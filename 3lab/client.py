# Асинхронность
import asyncio
# Для работы с HTTP сервером
import httpx
# Для работы с каналом Websocket
import websockets
# Для более стабильной обработки спсика команд 
from typing import Dict, Callable
# Для стабильной работы ввода в асинхронном приложении
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
# Эндпоинты
from app.api.endpoints import FastApiServerInfo
from app.websocket.endpoints import WebsocketInfo
# Настрйоки сервера (в идеале их бы захардкодить чтобы приложение могло работать где угодно) 
from app.core.config import Settings
# Небольшие и нужные импорты
import json
import os, sys

# Класс приложения
class AsyncClient:
    def __init__(self):
        # Путь к серверу HTTP
        self.base_url = f"http://{Settings.IP}:{Settings.PORT}"
        # Путь к серверу Celery + Redis  
        self.ws_url = f"ws://{Settings.IP}:{Settings.PORT}/ws/{WebsocketInfo.NOTIFICATIONS}"
        # Уникальный токен пользователя
        self.user_token: str = None
        # email пользователя
        self.user_email: str = None
        # Состояние программы
        self.running = True
        # PromtSession позволяет нормально работать с вводом в асинхронном приложении
        self.session = PromptSession()
        # Список команд
        self.commands: Dict[str, Callable] = {
            "login": self.login,
            "registr": self.register,
            "task": self.create_task,
            "cls": self.clear_console,
            "exit": self.exit,
            "add_corpus": self.upload_corpus,
            "get_corpuses": self.courpuses,
            "search": self.search
        }
        # Задача Websocket
        self.ws_task: asyncio.Task = None
        # Задача внутри консоли пользователя
        self.input_task: asyncio.Task = None
        # Список активныз задач с уведомелниями от Websocket
        self.active_tasks = list()
    # Функция вывода уведомлений от задач с Websocket
    async def show_notification(self, message: str):
        with patch_stdout():
            print(f"[УВЕДОМЛЕНИЕ]: {message}")
            sys.stdout.flush()
    
    # Префикс перед каждой вводимой командо 
    # формат [имя_пользователя@уникальный_токен]
    async def safe_print(self, message: str):
        with patch_stdout():
            prefix = f"[{self.user_email.split('@')[0]}@{self.user_token}]" if self.user_token else "[guest@anon]"
            print(f"{prefix} --> {message}\n", end="")
            sys.stdout.flush()
    # Слушатель канала Websocket
    async def websocket_listener(self):
        while self.running:
            try:
                # Подключение к каналу Websocket
                async with websockets.connect(self.ws_url) as ws:
                    async for message in ws:
                        data = json.loads(message)
                        # Смотрю на id задачи уведомление которой получил
                        # если она совпадает с id какой-то активной задачи закрпелнной за клиентом
                        # то вывожу уведомление и удаляю из id из активных задач 
                        if data['task_id'] in self.active_tasks:
                            await self.show_notification(json.dumps(data, ensure_ascii=False))
                            # Как только задача выоплнена - она удаляется из списка активных задач пользователя
                            if data["status"] == "done":
                                self.active_tasks.remove(data['task_id'])

            except Exception as e:
                await self.safe_print(f"WebSocket error: {str(e)}")
                await asyncio.sleep(5)
    # Функция авторизации
    async def login(self):
        email = await self.session.prompt_async("Email: ")
        # В password скртый ввод 
        password = await self.session.prompt_async("Password: ", is_password=True)
        self.session.is_password = False
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # отправляю запрос
                response = await client.post(
                    # В какой эндпоинт
                    f"{self.base_url}{FastApiServerInfo.LOGIN_ENDPOINT}",
                    # Тело запроса
                    json={"email": email, "password": password}
                )
                # Обработка статусов запроса
                # Все хорошо, сразу же авторизуем нового пользователя
                if response.status_code == 200:
                    data = response.json()
                    self.user_token = data['token']
                    self.user_email = data['email']
                    await self.safe_print("Успешная авторизация!")
                else:
                    await self.safe_print(f"Ошибка: {response.text}")
                    
            except Exception as e:
                await self.safe_print(f"Ошибка соединения: {str(e)}")
    # Функция регистрации нового пользователя
    async def register(self):
        email = await self.session.prompt_async("Email: ")
        # В password скртый ввод 
        password = await self.session.prompt_async("Password: ", is_password=True)
        self.session.is_password = False
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # отправляю запрос
                response = await client.post(
                    # В какой эндпоинт
                    f"{self.base_url}{FastApiServerInfo.SIGN_UP_ENDPOINT}",
                    # Тело запроса
                    json={"email": email, "password": password}
                )
                # Обработка статусов запроса
                # Все хорошо, сразу же авторизуем нового пользователя
                if response.status_code == 200:
                    data = response.json()
                    self.user_token = data['token']
                    self.user_email = data['email']
                    await self.safe_print("Регистрация успешна!")
                else:
                    await self.safe_print(f"Ошибка: {response.text}")
                    
            except Exception as e:
                await self.safe_print(f"Ошибка соединения: {str(e)}")
    # Функция добавления корпуса текста 
    async def upload_corpus(self):
        corpus_name = await self.session.prompt_async("Название корпуса: ") 
        text = await self.session.prompt_async("Корпус: ")
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # Если не произведена авторизация, то запрещается выполнять заадчу
                # потому что задача привязана к пользователю и, в случае двух неавторизованных пользователей
                # обоим будут приходить уведомления о задачах друг друга 
                if not self.user_token:
                    raise Exception("Необходима авторизация!") 
                # отправляю запрос
                response = await client.post(
                    # В какой эндпоинт
                    f"{self.base_url}{FastApiServerInfo.UPLOAD_CORPUS_ENDPOINT}",
                    # Тело запроса
                    json={"corpus_name": corpus_name, "text": text}
                )
                # Обработка статусов запроса
                # Все хорошо, уведомляем пользователя
                if response.status_code == 200:
                    await self.safe_print("Корпус успешно добавлен!")
                else:
                    await self.safe_print(f"Ошибка: {response.text}")
                    
            except Exception as e:
                await self.safe_print(f"Ошибка соединения: {str(e)}")
    # Функция вывода всех корпусов текста 
    async def courpuses(self):
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # Если не произведена авторизация, то запрещается выполнять заадчу
                # потому что задача привязана к пользователю и, в случае двух неавторизованных пользователей
                # обоим будут приходить уведомления о задачах друг друга 
                if not self.user_token:
                    raise Exception("Необходима авторизация!") 
                # отправляю запрос
                response = await client.post(
                    # В какой эндпоинт
                    f"{self.base_url}{FastApiServerInfo.CORPUSES}",
                    # Тело запроса
                    json={}
                )
                # Обработка статусов запроса
                # Все хорошо, вывожу список всех существующих корпусов
                if response.status_code == 200:
                    data = response.json()
                    for corpus_dict in data["corpuses"]: 
                        print(f"Id: {corpus_dict["id"]} | Name: {corpus_dict["name"]}")
                else:
                    await self.safe_print(f"Ошибка: {response.text}")
                    
            except Exception as e:
                await self.safe_print(f"Ошибка соединения: {str(e)}")
    # Тестовая фунцкия требующая уведомлений через websocket + redis
    async def create_task(self):
        # Тестовый ввод
        # url = await self.session.prompt_async("Тестовый ввод: ")
        # Асинхронная работа с сервером HTTP
        async with httpx.AsyncClient() as client:
            try:
                # Если не произведена авторизация, то запрещается выполнять заадчу
                # потому что задача привязана к пользователю и, в случае двух неавторизованных пользователей
                # обоим будут приходить уведомления о задачах друг друга 
                if not self.user_token:
                    raise Exception("Необходима авторизация!") 
                # отправляю запрос
                response = await client.post(
                    # В какой эндпоинт
                    f"{self.base_url}/tasks/parse",
                    # Сам запрос
                    json = {}, # {"url": url},
                    # Заголовок запроса с токеном пользователя
                    headers={"Authorization": f"Bearer {self.user_token}"}
                )
                # Закидываю соответствующий клиенту id в активные задачи 
                self.active_tasks.append(response.json().get('task_id'))
                
            except Exception as e:
                await self.safe_print(f"Ошибка: {str(e)}")
    # Функция поиска заданного слова в заданном по id корпусе текста
    async def search(self):
        corpus_id = await self.session.prompt_async("Id корпуса: ")
        word = await self.session.prompt_async("Искомое слово: ")
        algorithm = await self.session.prompt_async("Название алгоритмы: ")
        async with httpx.AsyncClient() as client:
            try:
                # Если не произведена авторизация, то запрещается выполнять заадчу
                # потому что задача привязана к пользователю и, в случае двух неавторизованных пользователей
                # обоим будут приходить уведомления о задачах друг друга 
                if not self.user_token:
                    raise Exception("Необходима авторизация!") 
                # отправляю запрос
                response = await client.post(
                    # В какой эндпоинт
                    f"{self.base_url}/tasks/{WebsocketInfo.SEARCH_ALGORITHM}",
                    # Сам запрос
                    json = {"word": word, "algorithm": algorithm, "corpus_id": corpus_id},
                    # Заголовок запроса с токеном пользователя
                    headers={"Authorization": f"Bearer {self.user_token}"}
                )
                # Закидываю соответствующий клиенту id в активные задачи 
                self.active_tasks.append(response.json().get('task_id'))
                
            except Exception as e:
                await self.safe_print(f"Ошибка: {str(e)}")
    # Функция команды очистки консоли
    async def clear_console(self):
        os.system("cls" if os.name == "nt" else "clear")
        await self.safe_print("Консоль очищена")
    # Функция команды завершения работы клиента
    async def exit(self):
        self.running = False
        await self.safe_print("Завершение работы...")
        sys.exit()
    # Обработчик всех вводимых команд
    async def command_handler(self):
        while self.running:
            try:
                command = await self.session.prompt_async(
                    "Введите команду: ",
                    refresh_interval=0.1
                )
                
                if command in self.commands:
                    await self.commands[command]()
                elif command == "help":
                    await self.safe_print("Доступные команды: " + ", ".join(self.commands))
                else:
                    await self.safe_print("Неизвестная команда")

                    
            except KeyboardInterrupt:
                await self.exit()
            except Exception as e:
                await self.safe_print(f"Ошибка: {str(e)}")
    # Оснвоная функция приложения
    async def run(self):
        # Цикл для прослушки канала Websocket
        self.ws_task = asyncio.create_task(self.websocket_listener())
        # Цикл для обработки задач пользователя
        self.input_task = asyncio.create_task(self.command_handler())
        
        await asyncio.gather(
            self.ws_task,
            self.input_task,
            return_exceptions=True
        )

if __name__ == "__main__": 
    client = AsyncClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        pass