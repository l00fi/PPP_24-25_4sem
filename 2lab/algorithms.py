# Функции для замеров времени
import time
from functools import wraps

# Декоратор для замера времени работы функции
def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        # Вызов исходной функции
        result = func(*args, **kwargs) 
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        return result, elapsed
    return wrapper

# Расстояние Левенштейна реалзую классом (более простой импорти)
class LevenshteinDistance:
    # Итераиционная функция расстояния Левенштейна
    # https://ru.wikipedia.org/wiki/%D0%A0%D0%B0%D1%81%D1%81%D1%82%D0%BE%D1%8F%D0%BD%D0%B8%D0%B5_%D0%9B%D0%B5%D0%B2%D0%B5%D0%BD%D1%88%D1%82%D0%B5%D0%B9%D0%BD%D0%B0
    def d(self, i, j, Si, Sj):
        if i == -1 and j == -1:
            return 0
        elif j == -1 and i >= 0:
            return i
        elif i == -1 and j >= 0:
            return j
        else:
            return min([
                self.d(i, j - 1, Si, Sj),
                self.d(i - 1, j, Si, Sj),
                self.d(i - 1, j - 1, Si, Sj) - 1 if Si[i] == Sj[j] else 0
                ])
    # Функция нахождения ближайших слов, заранее задано одно ближайшее
    @measure_time
    def find(self, S, target, nearest_number=1):
        # Запоминаем список слов и таргет 
        self.S_array = S.split(" ")
        self.target = target
        # Проверка крайних значений
        if nearest_number > len(self.S_array):
            return "error: number greater then corpus lenght"
        elif nearest_number <= 0:
            return "error: incorrect value"
        # Для каждого отдельного слова считаем расстояние
        lev_dist = []
        for _ in self.S_array:
            # Изначально считаем что слова абослютно разные
            distance = 0
            for i in range(len(_)):
                for j in range(len(self.target)):
                    distance += self.d(i, j, _, self.target)
            lev_dist.append(distance)
        # Для нахождения K ближайших слов формирую список из (индекс, расстояние)
        dist_and_ind = [(i, lev_dist[i]) for i in range(len(lev_dist))]
        # Сортирую созданные список по расстоянию в порядке возрастания
        dist_and_ind.sort(key = lambda obj: obj[1], reverse=False)
        # Возвращаю набор слов, соответствующих ему расстояний и N ближайших заданному
        return {
            "results": [{"word": self.S_array[_[0]],
                         "distance": _[1]} for _ in dist_and_ind[:nearest_number]]
        }
    
# Метод N-грамм
class NGrams:
    # Грама - пересекающиеся подмножества из множества слова, притом такие что 
    # разница соседних подножеств равна символам в начале и конце окна длинны N  
    # Также в функции присутствует возможность уменьшить граму на заданное число
    def ngrams_split(self, word, new_N = False, N = 0):
        if new_N:
            return [word[i:i + N] for i in range(len(word) - N + 1)]
        else:
            return [word[i:i + self.N] for i in range(len(word) - self.N + 1)]
    
    def ngrams_compare(self, word_one, word_two, new_N = False, N = 0):
        # В случае если длинна слова меньше длины грамы, то длинна грамы ставноится равной 
        # длинне этого слова
        if new_N:
            grams_word_one = self.ngrams_split(word_one, new_N, N)
            grams_word_two = self.ngrams_split(word_two, new_N, N)
        else:
            grams_word_one = self.ngrams_split(word_one)
            grams_word_two = self.ngrams_split(word_two)
        # Подсчитываю количество одинаковых грам
        equal_grams = 0
        i, j = 0, 0
        while i < len(grams_word_two):
            if grams_word_two[i] == grams_word_one[j]:
                equal_grams += 1
                i += 1
                j = 0
            if j < len(grams_word_one) - 1:
                j += 1
            else:
                i += 1
                j = 0
        return equal_grams     

    # Функция нахождения ближайших слов, заранее задано одно ближайшее
    @measure_time
    def find(self, S, target, nearest_number=1, N = 2):
        # Запоминаем список слов и таргет 
        self.S_array = S.split(" ")
        self.target = target
        # Длинна граммы
        if N <= 0:
            self.N = 1
        else:
            self.N = N
        # Проверка крайних значений
        if nearest_number > len(self.S_array):
            return "error: number greater then corpus lenght"
        elif nearest_number <= 0:
            return "error: incorrect value"
        # Для каждого отдельного слова считаем расстояние
        grams_dist = []
        for _ in self.S_array:
            # Разделяю на N-грамм оба слова и считаю сходства
            # Если длинна слова меньше грамы, то его не стоит рассматривать 
            if len(_) >= self.N:
                grams_dist.append(self.ngrams_compare(_, self.target))
            else:
                grams_dist.append(self.ngrams_compare(_, self.target, True, len(_)))
        # Для нахождения K ближайших слов формирую список из (индекс, расстояние)
        dist_and_ind = [(i, grams_dist[i]) for i in range(len(grams_dist))]
        # Сортирую созданные список по расстоянию в порядке возрастания
        dist_and_ind.sort(key = lambda obj: obj[1], reverse=True)
        # Возвращаю набор слов, соответствующих ему расстояний и N ближайших заданному
        return {
            "results": [{"word": self.S_array[_[0]],
                         "distance": _[1]} for _ in dist_and_ind[:nearest_number]]
        }

def agorithms_list():
    return [{"name": "levenshtein",
             "func": LevenshteinDistance()},
             {"name": "ngrams",
             "func": NGrams()}]

# text = "hello world here i am test! ks_study"
# target = "worl"

# res, time = LevenshteinDistance().find(text, target, 2)
# res["time"] = time
# print(res)