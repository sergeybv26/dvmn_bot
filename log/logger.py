"""Модуль настройки логгера проекта"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys


class TelegramLogsHandler(logging.Handler):
    """Обработчик логов. Отправляет логи в Телеграм"""

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record) -> None:
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


LOG_FORMATTER = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'bot-app.log')

STREAM_HANDLER = logging.StreamHandler(sys.stdout)
STREAM_HANDLER.setFormatter(LOG_FORMATTER)
STREAM_HANDLER.setLevel(logging.INFO)

LOG_FILE = RotatingFileHandler(PATH, maxBytes=2000, backupCount=2, encoding='utf-8')
LOG_FILE.setFormatter(LOG_FORMATTER)

LOGGER = logging.getLogger('bot')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(logging.DEBUG)
