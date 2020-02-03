

# Класс для представления полей таблицы.
class TableStyle:

    # Представление зачета в описании стиля таблицы
    test = 'Зач'
    # Представление экзамена в описании стиля таблицы
    exam = 'Экз'
    # Первое поле таблицы
    first_last_name = 'Фамилия Имя'
    # Название поля таблицы для зачета
    test_field = 'Зачет'
    # Название поля таблицы для экзамена
    exam_field = 'Экзамен'

    # Список полей таблицы
    fields = []

    # file_name -- файл с описанием стиля таблицы
    # Стиль -- список лабораторных/Курсовых/Контрольных/... работ в течение курса,
    # а также наличие зачета и экзамена
    def __init__(self, file_name):
        self.fields.append(self.first_last_name)
        with open(file_name) as input:
            self.fields += (input.read().splitlines())
            input.close()
        if self.test in self.fields:
            self.fields = [v for v in self.fields if v != self.test]
            self.fields.append(self.test_field)
        if self.exam in self.fields:
            self.fields = [v for v in self.fields if v != self.exam]
            self.fields.append(self.exam_field)