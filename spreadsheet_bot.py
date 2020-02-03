import telebot
import requests
from re import fullmatch
from enum import Enum
from google_tables import TableInterface
from tg_bot import bot_config as config

"""
Init Google spreadsheet Table Interface
"""

tables_api = TableInterface("client_secret.json")

"""
Bot's code
"""


class BotStatus(Enum):
    NORMAL_STATE = 1
    WAIT_TABLE_FORMAT = 2
    WAIT_GROUP_LIST = 3
    CREATING_TABLE = 4


class CreationParams:
    def __init__(self):
        self.table_title = None
        self.table_directory = None
        self.group_file = None
        self.table_file = None
        self.group_name = None
        self.user_email = None


bot = telebot.TeleBot(config.TOKEN)
bot_status = BotStatus.NORMAL_STATE
creation_params = CreationParams()


@bot.message_handler(commands=["help"])
def help_command(message):
    text = "Команды:\n\n" \
           "/create title e-mail -- создать документ Google spreadsheet\n" \
           " - title -- заголовок документа (без пробелов)\n" \
           " - e-mail -- пользователь, которому необходимо предоставить доступ к созданной таблице.\n" \
           "После отправки команды необходимо выслать файл с форматом таблицы; затем -- файл со списком группы. " \
           "Название файла группы должно соответствовать ее номеру (\"NUM[_NUM][.txt]\").\n" \
           "После успешного создания таблицы бот присылает адрес таблицы на сервисе Google Spreadsheets.\n\n" \
           "/getTables -- вывести список созданных пользователем таблиц."
    bot.send_message(message.chat.id, text)


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

    global creation_params
    creation_params.table_directory = message.from_user.id
    print(creation_params.table_directory)
    creation_params.table_title = command_args[1]
    creation_params.user_email = command_args[2]

    global bot_status
    bot_status = BotStatus.WAIT_TABLE_FORMAT
    text = "Отправьте файл с форматом таблицы"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda message: \
        message.document is not None and \
        message.document.mime_type == 'text/plain' and bot_status == BotStatus.WAIT_TABLE_FORMAT,
                     content_types=['document'])
def handle_table_format_file(message):
    global creation_params
    creation_params.table_file = message.document.file_id
    text = "Теперь отправьте файл со списком группы"
    bot.send_message(message.chat.id, text)

    global bot_status
    bot_status = BotStatus.WAIT_GROUP_LIST


@bot.message_handler(func=lambda message: \
        message.document is not None and \
        message.document.mime_type == 'text/plain' and bot_status == BotStatus.WAIT_GROUP_LIST,
                     content_types=['document'])
def handle_group_format_file(message):
    file_name = message.document.file_name.split(sep='.', maxsplit=1)[0]
    if not fullmatch("\d+(_\d+)?(\.txt)?", file_name):
        bot.send_message(message.chat.id, "Неверный формат названия файла. Переименуйте файл и отправьте заново.")
        return

    global creation_params
    creation_params.group_file = message.document.file_id
    creation_params.group_name = file_name

    global bot_status
    bot_status = BotStatus.CREATING_TABLE
    bot.send_message(message.chat.id, "Создание таблицы...")
    table_url = __create_table(message.chat.id)
    bot.send_message(message.chat.id, "Таблица успешно создана.\nURL: " + table_url)

    bot_status = BotStatus.NORMAL_STATE


@bot.message_handler(commands=["stop"])
def stop_command(message):
    global creation_params
    creation_params = CreationParams()
    global bot_status
    bot_status = BotStatus.NORMAL_STATE
    bot.send_message(message.chat.id, "Отмена всех действий")


@bot.message_handler(content_types=["text"])
def echo(message):
    bot.send_message(message.chat.id, message.text)


def __create_table(chat_id):
    bot.send_message(chat_id, "Загрузка файлов формата таблицы и списка группы.")

    # TODO: try-except
    global creation_params
    table_file_info = bot.get_file(creation_params.table_file)
    table_file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.TOKEN, table_file_info.file_path))
    with open("temp_files/temp_table_style", "w") as temp_table_style:
        temp_table_style.write(table_file.content.decode("utf-8"))
        temp_table_style.close()

    group_file_info = bot.get_file(creation_params.group_file)
    group_file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.TOKEN, group_file_info.file_path))
    with open("temp_files/temp_group_list", "w") as temp_group_list:
        temp_group_list.write(group_file.content.decode("utf-8"))
        temp_group_list.close()

    bot.send_message(chat_id, "Загрузка файлов успешно завершена.")

    # TODO try-except
    url = tables_api.create_spreadsheet(creation_params.table_title, creation_params.table_directory,
                                        creation_params.group_name)

    return url


print(bot.get_me())

bot.polling(none_stop=True)
