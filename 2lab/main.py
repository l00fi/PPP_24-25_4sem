# Это база
from fastapi import FastAPI
# Схемы
from app.schemas.schemas import User, Corpus, AlgorithmCall
# Для генерации токена
import secrets
# Работаем с бд
import sqlite3
# Запуск сервера с заданным ip и портом
import uvicorn
from app.api.endpoints import FastApiServerInfo 
# Импортирую алгоритмы нечеткого поиска
from algorithms import agorithms_list, LevenshteinDistance, NGrams

# Адрес базы данных
DB_PATH = "app/db/database.db"

# fastAPI 
app = FastAPI()

# Говорит привет
@app.get("/")
async def root():
    return {"message": "Hello World"}

#--------------------------------------- Начало базовой части ---------------------------------------
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
        # # Прохожу по всем найденным и записываю их в existing_users
        # for row in rows:
        #     id, email, password = row
        #     existing_user = {
        #         "id": id,
        #         "email": email,
        #     }
        #     existing_users[id] = existing_user
        pass
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
    uvicorn.run(app, host=FastApiServerInfo.IP, port=FastApiServerInfo.PORT)