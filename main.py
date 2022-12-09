from pprint import pprint

import requests
import telegram
from environs import Env

env = Env()
env.read_env()

API_TOKEN = env('API_TOKEN')
BOT_TOKEN = env('BOT_TOKEN')
CHAT_ID = env('CHAT_ID')

headers = {
    'Authorization': f'Token {API_TOKEN}'
}


def get_checks_list():
    """Получает и выводит список проверок"""
    response = requests.get('https://dvmn.org/api/user_reviews/', headers=headers)

    print(response.status_code)
    pprint(response.json())


def send_get_request(url, query_params=None):
    """
    Выполняет отправку GET запроса и возвращает ответ
    :param url: url для отправки запроса
    :param query_params: параметры запроса
    :return: response
    """
    response = None
    try:
        response = requests.get(url, headers=headers, timeout=95, params=query_params)
    except requests.exceptions.ReadTimeout as err:
        print(err)
    except requests.exceptions.ConnectionError:
        pass
    return response


def bot_handler(response=None):
    """
    Реализует работу с телеграм-ботом. Формирует и отправляет сообщение о состоянии проверки задания.
    :param response: Ответ от API Devman
    """
    bot = telegram.Bot(token=BOT_TOKEN)
    if response:
        response = response.json()
        for attempt in response['new_attempts']:
            if attempt['is_negative']:
                result_msg = 'К сожалению, в работе нашлись ошибки.'
            else:
                result_msg = 'Преподавателю все понравилось, можно приступать к следующему уроку!'
            title = attempt['lesson_title']
            link = attempt['lesson_url']
            msg = f'У вас проверили работу "{title}". \n' \
                  f'Ссылка на урок: {link} \n' \
                  f'{result_msg}'
            bot.send_message(text=msg, chat_id=CHAT_ID)


def get_long_pooling():
    """Получает список проверок через long_pooling и отправляет в бот"""
    url = 'https://dvmn.org/api/long_polling/'

    response = send_get_request(url)
    while True:
        if response:
            data = response.json()
            if data['status'] == 'timeout':
                response = send_get_request(url, query_params={'timestamp': data['timestamp_to_request']})
            else:
                bot_handler(response)
                response = send_get_request(url)
        else:
            response = send_get_request(url)


if __name__ == '__main__':
    print('Телеграм-бот запущен!')
    get_long_pooling()

