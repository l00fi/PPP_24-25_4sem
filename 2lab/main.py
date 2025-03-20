# Это база
from fastapi import FastAPI
# Схемы
from app.schemas.schemas import User
# Для генерации токена
import secrets
# Работаем с бд
import sqlite3

# fastAPI 
app = FastAPI()

# Говорит привет
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Логинимся и проверяем, есть ли такой
@app.post("/sign-up/")
async def sign_up(user: User):
    token, id = None, None
    # Словарь для возврата в return
    existing_users = dict()
    # Соезинение с бд
    connection = sqlite3.connect("app/db/database.db")
    cursor = connection.cursor()
    # Запрос на поиск ползователя по паролю и почте
    cursor.execute("SELECT * FROM Users WHERE email = ?", 
                   (user.email,))
    rows = cursor.fetchall()
    if rows:
        # Прохожу по всем найденным и записываю их в existing_users
        for row in rows:
            id, email, password, token = row
            existing_user = {
                "id": id,
                "email": email,
                "token": token  
            }
            existing_users[id] = existing_user
    else:
        # Делаю токен
        token = secrets.token_urlsafe()
        # Запрос на добавление новую строку 
        cursor.execute("INSERT INTO Users (email, password, token) VALUES (?, ?, ?)", 
                    (user.email, user.password, token))
        # Добавляю в словарь для return
        connection.commit()
        #Получаю id
        cursor.execute("SELECT id FROM Users WHERE email = ? AND password = ?", 
                    (user.email, user.password))
        id = cursor.fetchall()[0][0]
        # Записываю в existing_users
        existing_users[id] = {
                "id": id,
                "email": user.email,
                "token": token  
            }
        
    connection.close()
    return existing_users