####################################################################################################
LOGO = '''\
       _                _     _       _       __                _
__   _| | __  _ __ __ _(_) __| |   __| | ___ / _| ___ _ __   __| | ___ _ __
\ \ / / |/ / | '__/ _` | |/ _` |  / _` |/ _ \ |_ / _ \ '_ \ / _` |/ _ \ '__|
 \ V /|   <  | | | (_| | | (_| | | (_| |  __/  _|  __/ | | | (_| |  __/ |
  \_/ |_|\_\ |_|  \__,_|_|\__,_|  \__,_|\___|_|  \___|_| |_|\__,_|\___|_|

by alfred richardsn'''
####################################################################################################
import sys

try:
    import vk_api
except ImportError:
    sys.exit('для работы vk raid defender необходима библиотека vk_api')

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

import re
import os
import pickle
import logging
from time import time
from getpass import getpass


DATA_FILE_NAME = 'vk_raid_helper.dat'

try:
    with open(DATA_FILE_NAME, 'rb') as f:
        data = pickle.load(f)
except FileNotFoundError:
    with open(DATA_FILE_NAME, 'wb') as f:
        data = {}
        pickle.dump(data, f)


def update_data():
    with open(DATA_FILE_NAME, 'wb') as f:
        pickle.dump(data, f)


logger = logging.getLogger('vk raid defender')
logger.setLevel(logging.INFO)
terminal_logger = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s.%(msecs).03d] %(message)s", datefmt="%H:%M:%S")
terminal_logger.setFormatter(formatter)
logger.addHandler(terminal_logger)
logger.propagate = False


def start_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(LOGO + '\n\n')


class VkSession(VkApi):
    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, token=token, **kwargs)

        self.vk = self.get_api()

    def start(self):
        start_screen()

        chat_ids = data.get('chat_ids')
        objectives = data.get('objectives')

        if chat_ids is not None and objectives is not None:
            answer = None
            while answer not in ('y', 'n', ''):
                answer = input('использовать ранее сохранённые данные для работы? (Y/n): ').lower()

                if answer in 'y':
                    request_info = False

                elif answer == 'n':
                    request_info = True

        else:
            request_info = True

        if request_info:
            chat_ids = list(map(int, input('введи айди конф, в которых нужно защищать рейдеров, через пробел: ').split()))
            objectives = list(map(int, input('введи айди защищаемых рейдеров: ').split()))

            answer = None
            while answer not in ('y', 'n', ''):
                answer = input('сохранить введённые данные для следующих сессий? (Y/n): ').lower()

                if answer in 'y':
                    data['chat_ids'] = chat_ids
                    data['objectives'] = objectives
                    update_data()

        self._chat_ids = chat_ids
        self._objectives = objectives

        start_screen()
        self.listen()

    def listen(self):
        logger.info('начинаю приём сообщений')

        limit_time = time()
        defend_counter = 0

        polling = VkLongPoll(self)

        try:
            for event in polling.listen():
                if not (event.type == VkEventType.MESSAGE_NEW and
                        event.chat_id is not None and
                        event.chat_id in self._chat_ids and
                        event.to_me):
                    continue

                event_dict = event.raw[7]

                if event_dict.get('source_act') == 'chat_kick_user' and event_dict['source_mid'] != event_dict['from']:
                    user_victim = int(event_dict['source_mid'])
                    if user_victim in self._objectives:

                        if time() - limit_time > 1:
                            limit_time = time()
                            defend_counter = 0

                        elif defend_counter >= 3:
                            continue

                        try:
                            self.vk.messages.addChatUser(chat_id=event.chat_id, user_id=user_victim)
                            defend_counter += 1
                            logger.info(f'{user_victim} был возвращён в конфу "{event.subject}"')
                        except Exception as e:
                            logger.error(f'не удалось вернуть {user_victim} в конфу "{event.subject}": "{e}"')

        except Exception as e:
            start_screen()
            logger.critical('произошла критическая ошибка, перезапускаюсь', exc_info=True)

        self.listen()


def main():
    print('для работы vk raid helper необходима авторизация')

    token = data.get('token')

    if token is not None:
        answer = None
        while answer not in ('y', 'n', ''):
            answer = input('использовать ранее сохранённые данные для авторизации? (Y/n): ').lower()

            if answer in 'y':
                do_auth = False

            elif answer == 'n':
                do_auth = True

    else:
        do_auth = True

    if do_auth:
        print('\nhttps://oauth.vk.com/authorize?client_id=6020061&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=69632&response_type=token\n')

        token = None
        while token is None:
            user_input = getpass('перейди по ссылке выше в любом веб-браузере, авторизируйся и вставь адресную строку веб-страницы, на которую было осуществлено перенаправление: ')
            token = re.search(r'(?:.*access_token=)?([a-f0-9]+).*', user_input)

        token = token.group(1)

        answer = None
        while answer not in ('y', 'n', ''):
            answer = input('сохранить введённые данные для следующих сессий? (Y/n): ').lower()

            if answer in 'y':
                data['token'] = token
                update_data()

    session = VkSession(token)
    try:
        session.start()
    except KeyboardInterrupt:
        print()
        sys.exit()


if __name__ == "__main__":
    main()