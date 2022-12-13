import requests
import telegram
from environs import Env


def send_bot_msg(response):
    """
    Реализует работу с телеграм-ботом. Формирует и отправляет сообщение о состоянии проверки задания.
    :param response: Ответ от API Devman
    """
    bot = telegram.Bot(token=BOT_TOKEN)
    if response.get('new_attempts'):
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


def get_long_pooling(url, _headers, _timestamp=None):
    """
    Получает список проверок через long_pooling и отправляет в бот
    :param url: str - url на который необходимо выполнить get запрос
    :param _headers: заголовки get запроса
    :param _timestamp: метка времени
    :return: dict - результат запроса
    """

    try:
        response = requests.get(url, headers=_headers, timeout=95, params={'timestamp': _timestamp})
        response.raise_for_status()
        _review_result = response.json()

        if 'error' in _review_result:
            raise requests.exceptions.HTTPError(_review_result['error'])

        return _review_result
    except requests.exceptions.ReadTimeout as err:
        print(err)
    except requests.exceptions.ConnectionError:
        print('Ошибка подключения!')


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
        review_result = get_long_pooling(URL, HEADERS, timestamp)
        if review_result['status'] == 'timeout':
            timestamp = review_result['timestamp_to_request']
        else:
            send_bot_msg(review_result)
