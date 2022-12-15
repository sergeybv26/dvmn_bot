import logging
import time
from textwrap import dedent

import requests
import telegram
from environs import Env

import log.logger


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
    LOGGER = logging.getLogger('bot')
    LOGGER.info('Телеграм-бот запущен!')

    env = Env()
    env.read_env()
    API_TOKEN = env('API_TOKEN')
    BOT_TOKEN = env('BOT_TOKEN')
    CHAT_ID = env('CHAT_ID')
    URL = 'https://dvmn.org/api/long_polling/'
    HEADERS = {
        'Authorization': f'Token {API_TOKEN}'
    }

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
