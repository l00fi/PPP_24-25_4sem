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

# Логинимся и проверяем, есть ли такой
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

@app.post(FastApiServerInfo.LOGIN_ENDPOINT)
async def login(user: User):
    token, id = None, None
    # Словарь для возврата в return
    existing_users = dict()
    # Соезинение с бд
    connection = sqlite3.connect("app/db/database.db")
    cursor = connection.cursor()
    # Запрос на поиск пользователя по паролю и почте
    cursor.execute("SELECT * FROM Users WHERE email = ? AND password = ?", 
                   (user.email,user.password))
    # Такой пользователь всегда один
    rows = cursor.fetchone()
    if rows:
        # Распаковываю данные о польщователе
        id, email, password = rows
        # Генерирую токен
        token = secrets.token_urlsafe()
        # Добавляю ответ
        existing_users[id] = {
                "id": id,
                "email": email,
                "token": token  
            }
    else:
        # Если введн не первый password, то возвращаю сообщение об ошибке
        connection.close()
        return {"Message": "Incorrect password"}
    
    connection.close()
    return existing_users

if __name__ == "__main__":
    uvicorn.run(app, host=FastApiServerInfo.IP, port=FastApiServerInfo.PORT)