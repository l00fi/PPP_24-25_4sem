# time нужно для иммитации длительности процесса
# json нужен, чтобы обрабатывать запросы 
import time, json
# Параметры сервера Celery
from app.celery.celery_app import celery_app
# Параметры сервера HTTP и Redis
from app.core.config import Settings
from app.schemas.schemas import AlgorithmCall
# Импортирую алгоритмы нечеткого поиска
from app.algorithms import agorithms_list, LevenshteinDistance, NGrams
# Работаем с бд
import sqlite3

# Адрес базы данных
DB_PATH = "app/db/database.db"

# В name явно объявляю путь и имя "тяжелого" процесса
@celery_app.task(bind=True, name="app.celery.tasks.long_running_parse")
def long_running_parse(self): # url: str
    # Открываю соединенеие с каналом Redis
    from redis import Redis
    r = Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT, db=0)
    # Пушим уведомление
    result = {"task_id": self.request.id, "status": "in progress"}
    r.publish("notifications", json.dumps(result))
    # пример “тяжёлой” операции
    time.sleep(5)
    # Пушим уведомление
    result = {"task_id": self.request.id, "status": "done"}
    r.publish("notifications", json.dumps(result))
    return result
        
# Тестируем алгоритмы написанные в algorithms.py
@celery_app.task(bind=True, name="app.celery.tasks.search_algorithm")
def search_algorithm(self, word: str, algorithm: str, corpus_id: str):
    # Открываю соединенеие с каналом Redis
    from redis import Redis
    # Уведомление о начале работы
    r = Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT, db=0)
    result = {"status": "started",
              "task_id": self.request.id, 
              "word": word,
              "algorithm": algorithm
              }
    r.publish("notifications", json.dumps(result))
    # Поиск необходимого алгоритмы 
    alg = 0
    for alg_info in agorithms_list():
        if alg_info["name"] == algorithm:
            alg = alg_info
    if alg == 0:
        return {"Message": "Algorithm with this name doesn`t exists"}
    # Соезинение с бд
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # Запрос на поиск корпсов с заданным именем
    cursor.execute("SELECT text FROM Corpuses WHERE id = ?",
                   (corpus_id,))
    rows = cursor.fetchone()
    print("!!!")
    if rows:
        # Выполнение алгоритма
        result, time = alg["func"].find(rows[0], word)
        # Возвращаю результат
        connection.close()
        # Уведомление о конце работы
        r = Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT, db=0)
        result = {"status": "done",
                "task_id": self.request.id, 
                "execution_time": time,
                "results": result
                }
        r.publish("notifications", json.dumps(result))
        return result
    else:
        connection.close()
        return {"Message": "No corpuses in this table"}