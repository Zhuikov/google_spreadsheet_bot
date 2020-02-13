import telebot
import requests
from telebot import types
from re import fullmatch
from enum import Enum
from google_tables import TableInterface
from tg_bot import bot_config as config

from pprint import pprint

"""Init Google spreadsheet Table Interface"""

tables_api = TableInterface("botsCreds.json")

"""User's status and tables maps"""

users_map = {}  # { user_id: UserStatus }
tables_map = {}  # { user_id: {id, name, link} }

"""Maps used in user's complex operations"""

creation_map = {}  # { user_id: CreationParams }
deletion_map = {}  # { user_id: *list of tables with equals name* }
att_map = {}  # { user_id: AttendanceLists }
sharing_map = {}  # { user_id: SharingParams }


class UserStatus(Enum):
    NORMAL_STATE = 1
    WAIT_TABLE_FORMAT = 2
    WAIT_GROUP_LIST = 3
    CREATING_TABLE = 4
    DELETING_TABLE = 5
    DELETING_TABLE_WAITING = 6
    SHARING_TABLE = 7
    SHARING_TABLE_WAITING = 8
    ATT_STATE = 9


class CreationParams:
    def __init__(self):
        self.table_title = None
        self.table_directory = None
        self.group_file = None
        self.table_file = None
        self.group_name = None


class SharingParams:
    # tables -- list of tables with equal name
    def __init__(self, tables, user_mail, role):
        self.tables = tables
        self.user_mail = user_mail
        self.role = role


class AttendanceLists:
    def __init__(self, students, spreadsheet_name):
        self.spreadsheet_name = spreadsheet_name
        self.current_index = 0
        self.students = students
        self.attendance = []


att_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = types.KeyboardButton("+")
button2 = types.KeyboardButton("-")
att_keyboard.add(button1, button2)

# TODO: read old users from file
"""Bot's code"""

bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=["help"])
def help_command(message):
    text = "Команды:\n\n" \
           "/create title -- создать документ Google spreadsheet.\n" \
           " - title -- заголовок документа (без пробелов).\n\n" \
           "После отправки команды необходимо выслать файл с форматом таблицы; затем -- файл со списком группы. " \
           "Название файла группы должно соответствовать ее номеру (\"NUM[_NUM][.txt]\").\n" \
           "После успешного создания таблицы бот присылает адрес таблицы на сервисе Google Spreadsheets.\n\n" \
           "/share e-mail role -- предоставить пользователю доступ к созданной таблице с указанной ролью.\n" \
           " - e-mail -- пользователь, которому необходимо предоставить доступ к созданной таблице,\n" \
           " - role -- права доступа R или W (r или w), где R -- доступ только для чтения, " \
           "W -- доступ для редактирования.\n" \
           "После успешной выдачи прав бот присылает адрес таблицы.\n\n" \
           "/get -- вывести список созданных пользователем таблиц.\n\n" \
           "/delete title -- удалить таблицу с указанным названием title.\n" \
           "В случае нескольких таблиц с одинаковым названием предоставляется выбор нужной таблицы.\n\n" \
           "/att table col -- начать выставление посещаемости студентов.\n" \
           " - table -- заголовок документа таблицы,\n" \
           " - col -- заголовок создаваемого столбца в таблице table.\n" \
           "В результате успешного выполнения команды в таблице создается дополнительный столбец с проставленной" \
           "посещаемостью студентов. В заметку столбца добавляется текущая дата.\n\n" \
           "/stop -- отменяет текущую операцию создания, удаления таблицы или процесс выставления посещаемости."
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["map"])
def __maps(message):
    print("user map")
    pprint(users_map)
    print("tables_map")
    pprint(tables_map)
    print("creation map")
    pprint(creation_map)
    print("deletion map")
    pprint(deletion_map)
    print("att_map")
    pprint(att_map)


@bot.message_handler(commands=["start"])
def create_command(message):
    users_map[message.from_user.id] = UserStatus.NORMAL_STATE
    user_tables = tables_api.get_spreadsheets(message.from_user.id)
    tables_map[message.from_user.id] = user_tables if user_tables is not None else []
    bot.send_message(message.chat.id, "Бот готов к работе. Список команд: /help")


@bot.message_handler(func=lambda message:
users_map[message.from_user.id] == UserStatus.NORMAL_STATE,
                     commands=["create"])
def create_command(message):
    command_args = message.text.split()
    if len(command_args) != 2:
        bot.send_message(message.chat.id, "Неверный формат команды. (см. /help)")
        return

    creation_params = CreationParams()
    creation_params.table_directory = message.from_user.id
    creation_params.table_title = command_args[1]
    creation_map[message.from_user.id] = creation_params

    users_map[message.from_user.id] = UserStatus.WAIT_TABLE_FORMAT
    bot.send_message(message.chat.id, "Отправьте файл с форматом таблицы")


@bot.message_handler(func=lambda message:
message.document is not None and
message.document.mime_type == 'text/plain' and
users_map[message.from_user.id] == UserStatus.WAIT_TABLE_FORMAT,
                     content_types=['document'])
def handle_table_format_file(message):
    creation_map[message.from_user.id].table_file = message.document.file_id

    users_map[message.from_user.id] = UserStatus.WAIT_GROUP_LIST
    bot.send_message(message.chat.id, "Теперь отправьте файл со списком группы")


@bot.message_handler(func=lambda message:
                     message.document is not None and
                     message.document.mime_type == 'text/plain' and
                     users_map[message.from_user.id] == UserStatus.WAIT_GROUP_LIST,
                     content_types=['document'])
def handle_group_format_file(message):
    file_name = message.document.file_name.split(sep='.', maxsplit=1)[0]
    if not fullmatch("\d+(_\d+)?(\.txt)?", file_name):
        bot.send_message(message.chat.id, "Неверный формат названия файла. Переименуйте файл и отправьте заново.")
        return

    creation_map[message.from_user.id].group_file = message.document.file_id
    creation_map[message.from_user.id].file_name = message.document.file_name

    users_map[message.from_user.id] = UserStatus.CREATING_TABLE

    creation_params = creation_map[message.from_user.id]

    try:
        created_table = __create_table(message.chat.id, creation_params)
    except Exception:
        bot.send_message(message.chat.id, "Ошибка при создании таблицы")
        return

    creation_map.pop(message.from_user.id, None)
    tables_map[message.from_user.id].append({"id": created_table["id"],
                                             "name": creation_params.table_title,
                                             "link": created_table["link"]})

    users_map[message.from_user.id] = UserStatus.NORMAL_STATE
    bot.send_message(message.chat.id, "Таблица успешно создана.\n" + created_table["link"])


@bot.message_handler(func=lambda message:
                     users_map[message.from_user.id] is not None and
                     users_map[message.from_user.id] == UserStatus.NORMAL_STATE,
                     commands=["share"])
def share_command(message):
    command_args = message.text.split()
    if len(command_args) != 4:
        bot.send_message(message.chat.id, "Наверное количество аргументов. См /help")
        return
    # command_args = ['/share', table_name, e-mail, role]

    if not fullmatch(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", command_args[2]):
        bot.send_message(message.chat.id, "Неверный формат e-mail адреса")
        return

    if not fullmatch(r"(R|r|W|w)", command_args[3]):
        bot.send_message(message.chat.id, "Неверный формат выдаваемых прав доступа. Необходимо R/r или W/w")
        return

    share_tables = list(filter(lambda x: x["name"] == command_args[1], tables_map[message.from_user.id]))

    if not share_tables:
        bot.send_message(message.chat.id, "Таблица \"" + command_args[1] + "\" не найдена")
        return

    if len(share_tables) == 1:
        users_map[message.from_user.id] = UserStatus.SHARING_TABLE
        try:
            url = tables_api.share_table(share_tables[0]["id"], command_args[2], command_args[3].lower())
        except Exception:
            bot.send_message(message.chat.id, "Ошибка при выдаче прав")
            users_map[message.from_user.id] = UserStatus.NORMAL_STATE
            return

        users_map[message.from_user.id] = UserStatus.NORMAL_STATE
        bot.send_message(message.chat.id, "Права на таблицу успешно предоставлены: " + url)
        return

    # Many tables with equal name
    sharing_map[message.from_user.id] = SharingParams(share_tables, command_args[2], command_args[3])
    users_map[message.from_user.id] = UserStatus.SHARING_TABLE_WAITING
    table_list = command_args[1] + ":"
    for i in range(len(share_tables)):
        current_line = "\n" + str(i) + ". " + share_tables[i]["link"]
        table_list += current_line
    bot.send_message(message.chat.id, "Выберите номер таблицы для выдачи прав")
    bot.send_message(message.chat.id, table_list)


@bot.message_handler(func=lambda message:
                     users_map[message.from_user.id] == UserStatus.SHARING_TABLE_WAITING,
                     content_types=["text"])
def deletion_table_number(message):
    message_text = message.text
    if not fullmatch("\d+", message_text):
        bot.send_message(message.chat.id, "Отправьте номер нужной таблицы.")
        return

    table_number = int(message_text)

    if table_number > len(sharing_map[message.from_user.id].tables):
        bot.send_message(message.chat.id, "Число должно быть меньше {0}."
                         .format(str(len(deletion_map[message.from_user.id]))))
        return

    url = tables_api.share_table(sharing_map[message.from_user.id].tables[table_number],
                                 sharing_map[message.from_user.id].user_mail,
                                 sharing_map[message.from_user.id].role)

    sharing_map.pop(message.from_user.id, None)
    users_map[message.from_user.id] = UserStatus.NORMAL_STATE
    bot.send_message(message.chat.id, "Права на таблицу успешно предоставлены: " + url)


@bot.message_handler(func=lambda message:
                     users_map[message.from_user.id] == UserStatus.NORMAL_STATE,
                     commands=["get"])
def get_command(message):
    if not tables_map[message.from_user.id]:
        bot.send_message(message.chat.id, "У вас пока нет таблиц")
        return

    text = "Список ваших таблиц:"
    for table in tables_map[message.from_user.id]:
        line = "\n" + table["name"] + ": " + table["link"]
        text += line
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["stop"])
def stop_command(message):
    if creation_map.pop(message.from_user.id, None) is not None:
        users_map[message.from_user.id] = UserStatus.NORMAL_STATE
        bot.send_message(message.chat.id, "Отмена создания таблицы")

    if deletion_map.pop(message.from_user.id, None) is not None:
        users_map[message.from_user.id] = UserStatus.NORMAL_STATE
        bot.send_message(message.chat.id, "Отмена удаления таблицы")

    if att_map.pop(message.from_user.id, None) is not None:
        users_map[message.from_user.id] = UserStatus.NORMAL_STATE
        bot.send_message(message.chat.id, "Отмена выставления посещаемости",
                         reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda message:
users_map[message.from_user.id] is not None and
users_map[message.from_user.id] == UserStatus.NORMAL_STATE,
                     commands=["delete"])
def delete_command(message):
    command_args = message.text.split()
    # command_args = ['/delete', table_name]

    if len(command_args) != 2:
        bot.send_message(message.chat.id, "Неверный формат команды, см. /help")
        return

    deleting_table = list(filter(lambda x: x["name"] == command_args[1], tables_map[message.from_user.id]))

    if not deleting_table:
        bot.send_message(message.chat.id, "Таблица не найдена")
        users_map[message.from_user.id] = UserStatus.NORMAL_STATE
        return

    if len(deleting_table) == 1:
        users_map[message.from_user.id] = UserStatus.DELETING_TABLE
        tables_api.del_spreadsheet_by_id(deleting_table[0]["id"])
        users_map[message.from_user.id] = UserStatus.NORMAL_STATE
        __remove_from_tables_map(message.from_user.id, deleting_table[0]["id"])
        bot.send_message(message.chat.id, "Таблица успешно удалена")
        return

    # Many tables with equal names
    deletion_map[message.from_user.id] = deleting_table
    users_map[message.from_user.id] = UserStatus.DELETING_TABLE_WAITING
    table_list = command_args[1] + ":"
    for i in range(len(deleting_table)):
        current_line = "\n" + str(i) + ". " + deleting_table[i]["link"]
        table_list += current_line
    bot.send_message(message.chat.id, "Выберите номер таблицы для удаления")
    bot.send_message(message.chat.id, table_list)


@bot.message_handler(func=lambda message:
users_map[message.from_user.id] == UserStatus.DELETING_TABLE_WAITING,
                     content_types=["text"])
def deletion_table_number(message):
    message_text = message.text
    if not fullmatch("\d+", message_text):
        bot.send_message(message.chat.id, "Отправьте номер нужной таблицы.")
        return

    table_number = int(message_text)

    if table_number > len(deletion_map[message.from_user.id]):
        bot.send_message(message.chat.id, "Число должно быть меньше {0}."
                         .format(str(len(deletion_map[message.from_user.id]))))
        return

    tables_api.del_spreadsheet_by_id(deletion_map[message.from_user.id][table_number]["id"])
    __remove_from_tables_map(message.from_user.id, deletion_map[message.from_user.id][table_number]["id"])

    deletion_map.pop(message.from_user.id, None)
    users_map[message.from_user.id] = UserStatus.NORMAL_STATE
    bot.send_message(message.chat.id, "Таблица успешно удалена")


@bot.message_handler(func=lambda message:
users_map[message.from_user.id] == UserStatus.NORMAL_STATE,
                     commands=["att"])
def att_command(message):
    command_args = message.text.split()

    if len(command_args) != 3:
        bot.send_message(message.chat.id, "Неверный формат команды, см. /help")
        return

    students_list = tables_api.get_students_list(message.from_user.id, command_args[1])

    if students_list is None:
        bot.send_message(message.chat.id, "Таблица не найдена")
        return

    if not students_list:
        bot.send_message(message.chat.id, "Список студентов пуст")
        return

    att_map[message.from_user.id] = AttendanceLists(students_list, command_args[1])
    att_map[message.from_user.id].attendance.append(command_args[2])
    users_map[message.from_user.id] = UserStatus.ATT_STATE

    bot.send_message(message.chat.id, att_map[message.from_user.id].students[0],
                     parse_mode="html", reply_markup=att_keyboard)


@bot.message_handler(func=lambda message:
users_map[message.from_user.id] == UserStatus.ATT_STATE,
                     content_types=["text"])
def att_student(message):
    text = message.text

    print(text)
    if text != "+" and text != "-":
        bot.send_message(message.chat.id, "Используйте - или +")
        bot.send_message(message.chat.id,
                         att_map[message.from_user.id].students[att_map[message.from_user.id].current_index],
                         parse_mode="html", reply_markup=att_keyboard)
        return

    att_map[message.from_user.id].attendance.append("-" if text == "-" else "'+")
    att_map[message.from_user.id].current_index += 1

    if len(att_map[message.from_user.id].students) > att_map[message.from_user.id].current_index:
        bot.send_message(message.chat.id,
                         att_map[message.from_user.id].students[att_map[message.from_user.id].current_index],
                         parse_mode="html", reply_markup=att_keyboard)
    else:
        bot.send_message(message.chat.id, "Выставление посещаемости...")
        tables_api.add_date_col(message.from_user.id, att_map[message.from_user.id].spreadsheet_name,
                                att_map[message.from_user.id].attendance)
        users_map[message.from_user.id] = UserStatus.NORMAL_STATE
        att_map.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "Посещаемость успешно выставлена",
                         reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(content_types=["text"])
def echo(message):
    bot.send_message(message.chat.id, message.text)


def __remove_from_tables_map(user_id, table_id):
    for i in range(len(tables_map[user_id])):
        if table_id == tables_map[user_id][i]["id"]:
            tables_map[user_id].pop(i)
            return


def __create_table(chat_id, creation_params):
    bot.send_message(chat_id, "Загрузка файлов формата таблицы и списка группы.")

    # TODO: try-except
    table_file_info = bot.get_file(creation_params.table_file)

    table_file = requests.get(
        'https://api.telegram.org/file/bot{0}/{1}'.format(config.TOKEN, table_file_info.file_path))
    table_style = list(filter(None, table_file.content.decode("utf-8").split('\n')))
    table_file.close()

    group_file_info = bot.get_file(creation_params.group_file)
    group_file = requests.get(
        'https://api.telegram.org/file/bot{0}/{1}'.format(config.TOKEN, group_file_info.file_path))
    group_list = list(filter(None, group_file.content.decode("utf-8").split('\n')))
    group_file.close()

    bot.send_message(chat_id, "Загрузка файлов успешно завершена.")

    # TODO try-except
    created_table = tables_api.create_spreadsheet(creation_params.table_title, creation_params.table_directory,
                                                  creation_params.group_name, table_style, group_list)

    return created_table


print(bot.get_me())

bot.polling(none_stop=True)
