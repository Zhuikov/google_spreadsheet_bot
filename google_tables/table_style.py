

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

    # table_style -- список полей таблицы - описание ее стиля.
    # Стиль -- список лабораторных/Курсовых/Контрольных/... работ в течение курса,
    # а также наличие зачета и экзамена
    def __init__(self, table_style):
        fields_ = [self.first_last_name]
        fields_.extend(table_style)
        if self.test in fields_:
            fields_ = [v for v in fields_ if v != self.test]
            fields_.append(self.test_field)
        if self.exam in fields_:
            fields_ = [v for v in fields_ if v != self.exam]
            fields_.append(self.exam_field)
        self.fields = fields_
