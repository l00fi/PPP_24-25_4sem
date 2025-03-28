
# Инструкция по сдаче лабораторных работ

---

## Процесс сдачи работ

1. Создайте форк данного репозитория. ![Screenshot from 2025-02-13 13-37-32](https://github.com/user-attachments/assets/bc11a729-4373-46e5-ac91-55daced4c430)

2. Заполните файл `student.json` по следующему шаблону:
```json
{
    "name_f" : "Иванов",
    "name_i" : "Иван",
    "name_o" : "Иванович",
    "group" : "ПМ23-1",
    "id" : "222222",
    "variant" : ""
}
```

3. Разместите код лабораторных работ в папке `*lab`.
4. Убедитесь, что лабораторные работы запускаются из рабочей директории `*lab` командой:
```bash
python3 *lab/main.py
```

5. Все необходимые зависимости должны быть указаны в файле `requirements.txt`.

## Важные замечания

- Работы проверяются на взаимный плагиат. Работы с уровнем плагиата более 70% не принимаются.
- В случае обнаружения плагиата:
    - Работа аннулируется.
    - Для получения баллов за эту работу необходимо выполнить дополнительное задание.
- При обнаружении плагиата в нескольких работах:
    - Баллы не ставятся никому из участников плагиата, или
    - Баллы получает только автор работы с более ранним коммитом.

## Общие критерии оценки

- Если программа не запускается, как указано в пункте 4, она не принимается.
- Если программа не работает на разных операционных системах: **-50%** от оценки.
- Если программа использует внутри себя зашитые переменные, которые могут повлиять на ее работоспособность в других файловых системах или на работоспособность других программ системы пагубным образом: **-50%** от оценки.
- При наличии более 10 нарушений PEP 8: **-10%** от оценки.
- За каждый сценарий, при котором программа падает с ошибкой: **-30%** от оценки.
- Если программа принимает пользовательский ввод, который приводит к ошибке: **-20%** от оценки.

**Пожалуйста, соблюдайте академическую честность и выполняйте задания самостоятельно.**
   
    
 