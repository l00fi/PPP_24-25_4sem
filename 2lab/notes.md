[Ссылка](https://fastapi.tiangolo.com/ru/tutorial/first-steps/) на офф. руководство FastAPI.

Важные замечания:
- По крайней мере понадобилось пересмотреть файловую структуру проекта для того, чтоюы всё заработало: теперь в app находится всё кроме папки alembic и main.py, в самой же папке app находится ```__init__.py```, из-за которого python при импорте воспринимает его как модуль и может добраться до models.py и достать оттуда констурктор таблицы ```User```.

Сервер - это ```server_script.py```, запускать из терминала командой ``` uvicorn main:app --host 127.0.0.1 --port 12000```, где **server_script** - название py файла, **server_app** - название переменной которой присвоено FastAPI.

Alembic - по сути git, но для бд в рамках одного проекта

Для того чтобы добавить alemic в проект делаем следующее:
- Переходим через консоль в папку проекта и пишем ```alembic init alembic```
- Создаётся папка alembic, в ней находим ```alembic.ini```, ищем строку ```sqlalchemy.url = ...``` и пишем ```sqlite:///(относительный путь к бд, которой желательно лежать в папке проекта)```
**Очень важно докинуть в папку app файл __init__.py (он может быть пустым), иначе python не будет понимать, что из app можно что-то вытащить**
- В файле ```env.py``` импортируем модель SQLAlchemy, например так ```from app.models import (класс которым назван конструктор таблицы)``` и редактируем строку ```target_metadata = (класс которым назван конструктор таблицы).metadata```

Теперь заставляем это работать:
- В командной строке пишем ```alembic revision --autogenerate -m "create users table"``` - это создаст в alemic/versions py-файл. Его можно отредактировать (а имено методы **upgrade** и **downgrade**), если есть желание и умение. Это у нас создалась та самая миграция (или коммит).
- Всё в той же командной строке пишем ```alembic upgrade head``` для применение миграции (коммита) и ```alembic downgrade -1``` чтобы откатиться на предыдущую миграцию (коммит) 

SQLAlchemy - автоматизация создания структур бд через python.

Пример кода ниже пишем в отедльном файле, а потом из него импортиуем нужный класс. 
```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

# Создаём базовый класс для моделей
Base = declarative_base()

# Определяем модель User
class User(Base):
    __tablename__ = 'users'  # Имя таблицы в базе данных

    # Колонки таблицы
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
```