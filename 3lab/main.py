# Это база
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from redis import Redis
import json
# Аинхронность
import asyncio
# Схемы
from app.schemas.schemas import User, Corpus, AlgorithmCall
# Для генерации токена
import secrets
# Работаем с бд
import sqlite3
# Запуск сервера с заданным ip и портом
import uvicorn
from app.api.endpoints import FastApiServerInfo 
from app.core.config import Settings 
# Запуск Celery
from app.celery.tasks import long_running_task
# Импортирую алгоритмы нечеткого поиска
from app.algorithms import agorithms_list, LevenshteinDistance, NGrams

# Адрес базы данных
DB_PATH = "app/db/database.db"

# fastAPI 
app = FastAPI()

#--------------------------------------- Начало базовой части ---------------------------------------

redis_client = Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    try:
        # Клиент отправляет task_id
        data = await websocket.receive_json()
        task_id = data.get("task_id")
        
        # Подписка на канал с task_id
        pubsub.subscribe(f"task_{task_id}")
        
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_json(json.loads(message["data"]))
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pubsub.unsubscribe()
        await websocket.close()

@app.post("/tasks")
def create_task(user_id: int):
    task = long_running_task.delay(user_id)
    return {"task_id": task.id}

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    task = long_running_task.AsyncResult(task_id)
    return {"status": task.status, "result": task.result}

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
    if not rows:
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
    return existing_users

# Словарь хранит информацию авторизованного пользователя
logged_user = {
    "id": -1,
    "email": "_@_._"
}
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
        # Добавляю ответ
        logged_user["id"] = id
        logged_user["email"] = email
    else:
        # Если введн не первый password, то возвращаю сообщение об ошибке
        connection.close()
        return {"Message": "Incorrect password"}
    
    connection.close()
    # Вместо возврата logged
    return {
        "id": logged_user["id"],
        "email": logged_user["email"],
        "token": token
    }

# Вывод информации об авторизованном пользователе
@app.post(FastApiServerInfo.USER_INFO_ENDPOINT)
async def login():
    return logged_user
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
        
# Тестируем алгоритмы написанные в algorithms.py
@app.post(FastApiServerInfo.SEARCH_ALGORITHM)
async def search_algorithm(call: AlgorithmCall):
    # Поиск необходимого алгоритмы 
    alg = 0
    for alg_info in agorithms_list():
        if alg_info["name"] == call.algorithm:
            alg = alg_info
    if alg == 0:
        return {"Message": "Algorithm with this name doesn`t exists"}
    # Соезинение с бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск корпсов с заданным именем
    cursor.execute("SELECT text FROM Corpuses WHERE id = ?",
                   (call.corpus_id,))
    rows = cursor.fetchone()
    if rows:
        # Выполнение алгоритма
        result, time = alg["func"].find(rows[0], call.word)
        result["time"] = time
        # Возвращаю результат
        connection.close()
        return result
    else:
        connection.close()
        return {"Message": "No corpuses in this table"}

if __name__ == "__main__":
    # Чтобы не прописывать каждый раз команду uvicorn main:app --host 127.0.0.1 --port 12000 
    # и удобно устанавливать нужный IP и PORT, всё выношу в класс FastApiServerInfo в app/api/models
    uvicorn.run(app, host=Settings.IP, port=Settings.PORT)