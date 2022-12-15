"""Модуль настройки логгера проекта"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

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
