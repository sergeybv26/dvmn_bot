import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from textwrap import dedent

import requests
import telegram
from environs import Env


class TelegramLogsHandler(logging.Handler):
    """Обработчик логов. Отправляет логи в Телеграм"""

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record) -> None:
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def send_bot_msg(_response, bot_token, chat_id):
    """
    Реализует работу с телеграм-ботом. Формирует и отправляет сообщение о состоянии проверки задания.
    :param _response: Ответ от API Devman
    :param bot_token: Токен API Телеграм
    :param chat_id: ID чата Телеграм
    """
    bot = telegram.Bot(token=bot_token)
    if _response.get('new_attempts'):
        for attempt in _response['new_attempts']:
            if attempt['is_negative']:
                result_msg = 'К сожалению, в работе нашлись ошибки.'
            else:
                result_msg = 'Преподавателю все понравилось, можно приступать к следующему уроку!'
            title = attempt['lesson_title']
            link = attempt['lesson_url']
            msg = dedent(f'''У вас проверили работу "{title}". 
            Ссылка на урок: {link} 
            {result_msg}''')

            bot.send_message(text=msg, chat_id=chat_id)


if __name__ == '__main__':
    env = Env()
    env.read_env()
    API_TOKEN = env('API_TOKEN')
    BOT_TOKEN = env('BOT_TOKEN')
    CHAT_ID = env('CHAT_ID')
    URL = 'https://dvmn.org/api/long_polling/'
    HEADERS = {
        'Authorization': f'Token {API_TOKEN}'
    }
    ADM_BOT_TOKEN = env('ADM_BOT_TOKEN')

    adm_bot = telegram.Bot(token=ADM_BOT_TOKEN)

    LOG_FORMATTER = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

    PATH = os.path.dirname(os.path.abspath(__file__))
    PATH = os.path.join(PATH, 'bot-app.log')

    STREAM_HANDLER = logging.StreamHandler(sys.stdout)
    STREAM_HANDLER.setFormatter(LOG_FORMATTER)
    STREAM_HANDLER.setLevel(logging.INFO)

    LOG_FILE = RotatingFileHandler(PATH, maxBytes=2000, backupCount=2, encoding='utf-8')
    LOG_FILE.setFormatter(LOG_FORMATTER)

    LOG_TLG = TelegramLogsHandler(tg_bot=adm_bot, chat_id=CHAT_ID)

    LOGGER = logging.getLogger('bot')
    LOGGER.addHandler(STREAM_HANDLER)
    LOGGER.addHandler(LOG_FILE)
    LOGGER.addHandler(LOG_TLG)
    LOGGER.setLevel(logging.DEBUG)

    LOGGER.info('Телеграм-бот запущен!')

    timestamp = None

    while True:

        try:
            response = requests.get(URL, headers=HEADERS, timeout=95, params={'timestamp': timestamp})
            response.raise_for_status()
            review_result = response.json()
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            LOGGER.error('Ошибка подключения!')
            time.sleep(30)
            continue

        if review_result['status'] == 'timeout':
            timestamp = review_result['timestamp_to_request']
        else:
            send_bot_msg(review_result, BOT_TOKEN, CHAT_ID)
            LOGGER.debug(f'Сообщение об изменении статуса проверки: {review_result}')
            timestamp = review_result['new_attempts'][0]['timestamp']
