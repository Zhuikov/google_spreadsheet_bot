import telebot
import requests
from re import fullmatch
from enum import Enum
from google_tables import TableInterface
from tg_bot import bot_config as config

from pprint import pprint

"""Init Google spreadsheet Table Interface"""

tables_api = TableInterface("botsCreds.json")

"""User's status map"""

users_map = {}

"""Creation params map"""

creation_map = {}

"""Bot's code"""


class BotStatus(Enum):
    NORMAL_STATE = 1
    WAIT_TABLE_FORMAT = 2
    WAIT_GROUP_LIST = 3
    CREATING_TABLE = 4
    DELETING_TABLE = 5


class CreationParams:
    def __init__(self):
        self.table_title = None
        self.table_directory = None
        self.group_file = None
        self.table_file = None
        self.group_name = None
        self.user_email = None

# TODO: read old users from file


bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=["help"])
def help_command(message):
    text = "Команды:\n\n" \
           "/create title e-mail -- создать документ Google spreadsheet\n" \
           " - title -- заголовок документа (без пробелов)\n" \
           " - e-mail -- пользователь, которому необходимо предоставить доступ к созданной таблице.\n" \
           "После отправки команды необходимо выслать файл с форматом таблицы; затем -- файл со списком группы. " \
           "Название файла группы должно соответствовать ее номеру (\"NUM[_NUM][.txt]\").\n" \
           "После успешного создания таблицы бот присылает адрес таблицы на сервисе Google Spreadsheets.\n\n" \
           "/get -- вывести список созданных пользователем таблиц.\n\n" \
           "/delete title -- удалить таблицу с указанным названием title\n" \
           "В случае нескольких таблиц с одинаковым названием предоставляется выбор нужной таблицы.\n\n" \
           "/stop -- отменяет текущую операцию\n\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["start"])
def create_command(message):
    users_map.update([(message.from_user.id, BotStatus.NORMAL_STATE)])
    bot.send_message(message.chat.id, "Бот готов к работе. Список команд: /help")


@bot.message_handler(commands=["create"])
def create_command(message):
    command_args = message.text.split()
    if len(command_args) != 3:
        bot.send_message(message.chat.id, "Неверный формат команды. (см. /help)")
        return

    if not fullmatch(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", command_args[2]):
        bot.send_message(message.chat.id, "Неверный формат e-mail адреса")
        return

    print(command_args)

    creation_params = CreationParams()
    creation_params.table_directory = message.from_user.id
    creation_params.table_title = command_args[1]
    creation_params.user_email = command_args[2]
    creation_map[message.from_user.id] = creation_params

    users_map[message.from_user.id] = BotStatus.WAIT_TABLE_FORMAT
    bot.send_message(message.chat.id, "Отправьте файл с форматом таблицы")


@bot.message_handler(func=lambda message: \
        message.document is not None and \
        message.document.mime_type == 'text/plain' and \
        users_map[message.from_user.id] == BotStatus.WAIT_TABLE_FORMAT, content_types=['document'])
def handle_table_format_file(message):

    creation_params = creation_map[message.from_user.id]
    creation_params.table_file = message.document.file_id
    creation_map[message.from_user.id] = creation_params

    users_map[message.from_user.id] = BotStatus.WAIT_GROUP_LIST
    bot.send_message(message.chat.id, "Теперь отправьте файл со списком группы")


@bot.message_handler(func=lambda message: \
        message.document is not None and \
        message.document.mime_type == 'text/plain' and \
        users_map[message.from_user.id] == BotStatus.WAIT_GROUP_LIST, content_types=['document'])
def handle_group_format_file(message):

    file_name = message.document.file_name.split(sep='.', maxsplit=1)[0]
    if not fullmatch("\d+(_\d+)?(\.txt)?", file_name):
        bot.send_message(message.chat.id, "Неверный формат названия файла. Переименуйте файл и отправьте заново.")
        return

    creation_params = creation_map[message.from_user.id]
    creation_params.group_file = message.document.file_id
    creation_params.group_name = file_name
    creation_map[message.from_user.id] = creation_params

    users_map[message.from_user.id] = BotStatus.CREATING_TABLE
    bot.send_message(message.chat.id, "Создание таблицы...")
    table_url = __create_table(message.chat.id, message.from_user.id)
    bot.send_message(message.chat.id, "Таблица успешно создана.\nURL: " + table_url)

    creation_map.pop(message.from_user.id, None)
    users_map[message.from_user.id] = BotStatus.NORMAL_STATE


@bot.message_handler(commands=["get"])
def get_command(message):
    table_list = tables_api.get_spreadsheets(message.from_user.id)

    if table_list is None:
        bot.send_message(message.chat.id, "У вас пока нет таблиц")
        return

    text = "Список таблиц:"
    for table in table_list:
        text += "\n" + table["name"] + ": " + table["link"]
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["stop"])
def stop_command(message):
    global creation_params
    creation_params = CreationParams()
    global bot_status
    bot_status = BotStatus.NORMAL_STATE
    bot.send_message(message.chat.id, "Отмена всех действий")


@bot.message_handler(commands=["delete"])
def delete_command(message):
    command_args = message.text.split()

    if len(command_args) != 2:
        bot.send_message(message.chat.id, "Неверный формат команды, см. /help")
        return

    global bot_status
    bot_status = BotStatus.DELETING_TABLE
    del_result = tables_api.del_spreadsheet(message.from_user, command_args[1])

    if del_result is None:
        bot.send_message(message.chat.id, "Таблица не найдена")
        bot_status = BotStatus.NORMAL_STATE
        return

    if not del_result:
        bot.send_message(message.chat.id, "Таблица успешно удалена")
        bot_status = BotStatus.NORMAL_STATE
        return

    if len(del_result) > 1:
        table_list = command_args[1] + ":"
        for i in range(len(del_result)):
            current_table = "\n" + str(i) + ". " + del_result[i]["link"]
            table_list += current_table
        bot.send_message(message.chat.id, "Выберите необходимую таблицу для удаления")
        bot.send_message(message.chat.id, table_list)


# @bot.message_handler(content_types=["text"])


@bot.message_handler(content_types=["text"])
def echo(message):
    bot.send_message(message.chat.id, message.text)


def __create_table(chat_id, user_id):
    bot.send_message(chat_id, "Загрузка файлов формата таблицы и списка группы.")

    # TODO: try-except
    table_file_info = bot.get_file(creation_map[user_id].table_file)

    table_file = requests.get(
        'https://api.telegram.org/file/bot{0}/{1}'.format(config.TOKEN, table_file_info.file_path))
    table_style = list(filter(None, table_file.content.decode("utf-8").split('\n')))
    table_file.close()

    group_file_info = bot.get_file(creation_map[user_id].group_file)
    group_file = requests.get(
        'https://api.telegram.org/file/bot{0}/{1}'.format(config.TOKEN, group_file_info.file_path))
    group_list = list(filter(None, group_file.content.decode("utf-8").split('\n')))
    group_file.close()

    bot.send_message(chat_id, "Загрузка файлов успешно завершена.")

    # TODO try-except
    creation_params = creation_map[user_id]
    url = tables_api.create_spreadsheet(creation_params.table_title, creation_params.table_directory,
                                        creation_params.group_name, table_style, group_list)

    return url


print(bot.get_me())

bot.polling(none_stop=True)
