# Это база
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
import redis.asyncio as redis
# Аинхронность и другие нужные штуки
import asyncio, json, os
# Схемы
from app.schemas.schemas import User, Corpus, AlgorithmCall # , ParseRequest
# Для генерации токена
import secrets
# Работаем с бд
import sqlite3
# Запуск сервера с заданным ip и портом
import uvicorn
# Эндпоинты и настройки сервера
from app.api.endpoints import FastApiServerInfo 
from app.websocket.endpoints import WebsocketInfo
from app.core.config import Settings 
# Запуск задачи Celery
from app.celery.tasks import long_running_parse
# Здесь настрйока Celery
from app.celery.celery_app import celery_app
# Оттуда же вытаскиваю канал через который отправляются уведомления
from app.celery.celery_app import REDIS_BROKER
# "Тяжелые функции"
from app.celery.tasks import long_running_parse, search_algorithm

# Адрес базы данных
DB_PATH = "app/db/database.db"

# fastAPI 
app = FastAPI()

#--------------------------------------- менеджер WebSocket-соединений #---------------------------------------

# Этот класс нужен для того, чтобы обслуживать сразу несколько клиентов
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, msg: dict):
        text = json.dumps(msg)
        for ws in self.active:
            await ws.send_text(text)

manager = ConnectionManager()

#--------------------------------------- Начало базовой части ---------------------------------------

#--------------------------------------- Базовая часть, 3 работа ---------------------------------------

# Подключение к Redis и запуск слушателя при запуске сервера
@app.on_event("startup")
async def on_startup():
    # Глобальные переменные - зло, но голову ломать не хочу
    # Объявляю подключерие к redis глобальным, чтобы в дальнейшем можно было к нему обращатсья
    global redis
    # Слушаю канал для уведомлений
    redis = await redis.from_url(REDIS_BROKER, decode_responses=True)
    # запускаю в фоне цикл, который слушает канал
    asyncio.create_task(notify_loop())

async def notify_loop():
    sub = redis.pubsub()
    # Указываю, что подписывабсь на канал websocket - notifications
    await sub.subscribe(WebsocketInfo.NOTIFICATIONS)
    while True:
        msg = await sub.get_message(ignore_subscribe_messages=True, timeout=None)
        if msg and msg["data"]:
            data = json.loads(msg["data"])
            await manager.broadcast(data)
        await asyncio.sleep(0.01)  # не жрём 100% CPU

# точка входа WebSocket
@app.websocket(f"/ws/{WebsocketInfo.NOTIFICATIONS}")
async def ws_notifications(ws: WebSocket):
    # Ждём подключения клиента
    await manager.connect(ws)
    try:
        while True:
            # Ожидаю пинг от клиента
            await ws.receive_text()
    # Если клиент прервёт соединение, то закрываю канал для него
    except WebSocketDisconnect:
        manager.disconnect(ws)

# Тестовая функция для проверки связки Celery + Redis + REST API
@app.post("/tasks/parse")
async def run_parse():
    task = long_running_parse.delay()
    print(long_running_parse)
    return {"task_id": task.id}

#--------------------------------------- Конец базовой части, 3 часть #---------------------------------------

# Функция для запуска search_algorithm на Celery + Redis
@app.post(f"/tasks/{WebsocketInfo.SEARCH_ALGORITHM}")
async def run_search_algorithm(req: AlgorithmCall): # req: ParseRequest
    task = search_algorithm.delay(req.word, req.algorithm, req.corpus_id) # req.url
    return {"task_id": task.id}

# --------------------------------------

# Добавление нового пользователя в бд
@app.post(FastApiServerInfo.SIGN_UP_ENDPOINT)
async def sign_up(user: User):
    token, id = None, None
    # Словарь для возврата в return
    existing_users = dict()
    # Соезинение с бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск пользователя по почте
    cursor.execute("SELECT * FROM Users WHERE email = ?", 
                   (user.email,))
    rows = cursor.fetchall()
    if rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже зарегистрирован."
        )
    else:
        # Запрос на добавление новую строку 
        cursor.execute("INSERT INTO Users (email, password) VALUES (?, ?)", 
                    (user.email, user.password))
        # Добавляю в словарь для return
        connection.commit()
        #Получаю id
        cursor.execute("SELECT id FROM Users WHERE email = ? AND password = ?", 
                    (user.email, user.password))
        id = cursor.fetchall()[0][0]
        # Получаю токен
        token = secrets.token_urlsafe()
        # Записываю в existing_users
        existing_users[id] = {
                "id": id,
                "email": user.email,
                "token": token  
            }
        
    connection.close()
    return existing_users[id]

# Авторизация, если она не прошла, то возвращаю соответствующее сообщение
@app.post(FastApiServerInfo.LOGIN_ENDPOINT)
async def login(user: User):
    token, id = None, None
    # Соезинение с бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск пользователя по паролю и почте
    cursor.execute("SELECT * FROM Users WHERE email = ? AND password = ?", 
                   (user.email,user.password))
    # Такой пользователь всегда один
    rows = cursor.fetchone()
    if rows:
        # Распаковываю данные о пользователя
        id, email, password = rows
        # Генерирую токен
        token = secrets.token_urlsafe()
    else:
        # Если введн не первый password, то возвращаю сообщение об ошибке
        connection.close()
        return {"Message": "Incorrect password"}
    
    connection.close()
    # Вместо возврата logged
    return {
        "id": id, # logged_user["id"],
        "email": email, # logged_user["email"],
        "token": token
    }

#--------------------------------------- Конец базовой части ---------------------------------------

# Загрузка текста
@app.post(FastApiServerInfo.UPLOAD_CORPUS_ENDPOINT)
async def upload_corpus(corpus: Corpus):
    # Соезинение с бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск корпсов с заданным именем
    cursor.execute("SELECT * FROM Corpuses WHERE corpus_name = ?", 
                   (corpus.corpus_name,))
    rows = cursor.fetchall()
    if rows:
        # В случае существования корпуса текста с данными именем возвращаю ошибку
        connection.close()
        return {"Message": f"Corpus with name {corpus.corpus_name} already exists!"}
    else:
        # Запрос на добавление новоко корпуса  
        cursor.execute("INSERT INTO Corpuses (corpus_name, text) VALUES (?, ?)", 
                    (corpus.corpus_name, corpus.text))
        connection.commit()
        #Получаю id
        cursor.execute("SELECT id FROM Corpuses WHERE corpus_name = ?", 
                    (corpus.corpus_name,))
        id = cursor.fetchall()[0][0]
    
    connection.close()
    return {
        "corpus_id": id,
        "text": corpus.text
    }

# Возврат списка всех корпусов
@app.post(FastApiServerInfo.CORPUSES)
async def courpuses():
    # Соезинение с бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск корпсов с заданным именем
    cursor.execute("SELECT id, corpus_name FROM Corpuses")
    rows = cursor.fetchall()
    if rows:
        all_corpuses_info = []
        # Прохожу по всем возвращенным корпусам и привожу их к нужному виду (словарь)
        for row in rows:
            id, corpus_name = row
            all_corpuses_info.append({
                "id": id,
                "name": corpus_name,
            })
        
        connection.close()
        return {"corpuses": all_corpuses_info}
    else:
        connection.close()
        return {"Message": "No corpuses in this table"}

if __name__ == "__main__":
    # Чтобы не прописывать каждый раз команду uvicorn main:app --host 127.0.0.1 --port 12000 
    # и удобно устанавливать нужный IP и PORT, всё выношу в класс FastApiServerInfo в app/api/models
    uvicorn.run(app, host=Settings.IP, port=Settings.PORT)