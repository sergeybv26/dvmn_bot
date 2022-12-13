import time
from textwrap import dedent

import requests
import telegram
from environs import Env


def send_bot_msg(_response, bot_token):
    """
    Реализует работу с телеграм-ботом. Формирует и отправляет сообщение о состоянии проверки задания.
    :param _response: Ответ от API Devman
    :param bot_token: Токен API Телеграм
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

            bot.send_message(text=msg, chat_id=CHAT_ID)


if __name__ == '__main__':
    print('Телеграм-бот запущен!')

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
            print('Ошибка подключения!')
            time.sleep(30)
            continue

        if review_result['status'] == 'timeout':
            timestamp = review_result['timestamp_to_request']
        else:
            send_bot_msg(review_result, BOT_TOKEN)
            timestamp = review_result['new_attempts'][0]['timestamp']
