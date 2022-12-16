import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from textwrap import dedent

import requests
import telegram
from environs import Env

LOGGER = logging.getLogger('bot')


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


def main():
    env = Env()
    env.read_env()
    api_token = env('API_TOKEN')
    bot_token = env('BOT_TOKEN')
    chat_id = env('CHAT_ID')
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {api_token}'
    }
    adm_bot_token = env('ADM_BOT_TOKEN')

    adm_bot = telegram.Bot(token=adm_bot_token)

    log_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(filename)s %(message)s')

    path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(path, 'bot-app.log')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    stream_handler.setLevel(logging.INFO)

    log_file = RotatingFileHandler(path, maxBytes=2000, backupCount=2, encoding='utf-8')
    log_file.setFormatter(log_formatter)

    log_tlg = TelegramLogsHandler(tg_bot=adm_bot, chat_id=chat_id)

    LOGGER.addHandler(stream_handler)
    LOGGER.addHandler(log_file)
    LOGGER.addHandler(log_tlg)
    LOGGER.setLevel(logging.DEBUG)

    LOGGER.info('Телеграм-бот запущен!')

    timestamp = None

    while True:

        try:
            response = requests.get(url, headers=headers, timeout=95, params={'timestamp': timestamp})
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
            send_bot_msg(review_result, bot_token, chat_id)
            LOGGER.debug(f'Сообщение об изменении статуса проверки: {review_result}')
            timestamp = review_result['new_attempts'][0]['timestamp']


if __name__ == '__main__':
    main()
