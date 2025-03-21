# Это база
from fastapi import FastAPI
# Схемы
from app.schemas.schemas import User
# Для генерации токена
import secrets
# Работаем с бд
import sqlite3
# Запуск сервера с заданным ip и портом
import uvicorn
from app.api.endpoints import FastApiServerInfo 

# fastAPI 
app = FastAPI()

# Говорит привет
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Добавление нового пользователя в бд
@app.post(FastApiServerInfo.SIGN_UP_ENDPOINT)
async def sign_up(user: User):
    token, id = None, None
    # Словарь для возврата в return
    existing_users = dict()
    # Соезинение с бд
    connection = sqlite3.connect("app/db/database.db")
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
    connection = sqlite3.connect("app/db/database.db")
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

if __name__ == "__main__":
    # Чтобы не прописывать каждый раз команду uvicorn main:app --host 127.0.0.1 --port 12000 
    # и удобно устанавливать нужный IP и PORT, всё выношу в класс FastApiServerInfo в app/api/models
    uvicorn.run(app, host=FastApiServerInfo.IP, port=FastApiServerInfo.PORT)