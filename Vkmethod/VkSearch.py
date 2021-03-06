import requests
import json
import os
import datetime as dt
import time
from Date_base.DecorDB import DBConnect
from Date_base.DecorDB import db_connect


class VkSearch(DBConnect):
    """Класс методов поиска и сортировки из api-vk"""

    url = 'https://api.vk.com/method/'
    with open(os.path.join("Vkmethod", "token.txt"), encoding='utf-8') as file:
        token = [t.strip() for t in file.readlines()]
    token_bot = token[0]
    token = token[1:]

    def __init__(self):
        super().__init__()
        self.params = {'access_token': self.token[0], 'v': '5.131'}
        self.author = 0
        self.search_offset = 0
        self.offset_bd = 0
        # Флаг указывающий на необходимость брать данные по merging_user_id из БД,
        # а не из сервера VK
        self.merging_user_from_bd = False

    def __set_params(self, zero=True):
        """Установка параметров для get запроса при неудачном запросе"""
        self.author = 0 if zero else self.author + 1
        print(f'Токен заменен на >>> {self.author}!')
        self.params = {'access_token': self.token[self.author], 'v': '5.131'}

    def get_stability(self, method, params_delta, i=0):
        """
        Метод get запроса с защитой на случай блокировки токена
        При неудачном запросе делается рекурсивный вызов
        с другим токеном и установкой этого токена по умолчанию
        через функцию __set_params
        Для работы функции необходим текстовый файл token.txt с построчно записанными токенами
        В первую строку заносится токен от чат-бота.
        """
        print(f'Глубина рекурсии: {i}/токен: {self.author}')
        method_url = self.url + method
        response = requests.get(method_url, params={**self.params, **params_delta}).json()
        if 'response' in response:
            return response
        elif i == len(self.token) - 1:
            return False
        elif self.author < len(self.token) - 1:
            self.__set_params(zero=False)
        elif self.author == len(self.token) - 1:
            self.__set_params()
        count = i + 1  # счетчик стэков вызова
        return self.get_stability(method, params_delta, i=count)

    def __albums_id(self, owner_id):
        """
        Cоздает список, содержащий id альбомов пользователя
        """
        params_delta = {'owner_id': owner_id, 'need_system': '1'}
        response = self.get_stability('photos.getAlbums', params_delta)
        if response and response['response']['items']:
            albums_id = []
            for item in response['response']['items']:
                albums_id.append(item['id'])
            return albums_id

    def __photos_get(self, owner_id, album_id):
        """
        Получение данных по фотографиям из одного альбома (album_id) пользователя (owner_id)
        :return: список из словарей, содержащих photo_url и количество лайков по каждой фото
        """
        params_delta = {'owner_id': owner_id, 'album_id': album_id, 'extended': 1}
        response = self.get_stability('photos.get', params_delta)
        if response:
            photos_info = []
            for item in response['response']['items']:
                likes = item['likes']['count']
                count_likes = str(likes)
                # Добавляем словарь в список photos_info
                photos_info.append({
                    'photo_id': f"photo{owner_id}_{item['id']}",
                    'merging_user_id': owner_id,
                    # 'photo_url': photo_url,
                    'count_likes': count_likes
                })
            return photos_info

    @db_connect(table="Photo", method="insert")
    def top_photo(self, owner_id):
        """
        Поиск топ-3 фото пользователя по первому доступному альбому
        Декоратором данные заносятся в БД в таблицу photo
        """
        def key_sort(elem):
            return elem['count_likes']

        total_photos_info = []
        albums = self.__albums_id(owner_id)
        if albums:
            count = 0
            for album_id in albums:
                photo_info = self.__photos_get(owner_id, album_id)
                total_photos_info += photo_info
                count += 1
                if total_photos_info and len(total_photos_info) > 2:
                    return sorted(total_photos_info, key=key_sort, reverse=True)[:3]
                elif count == len(albums):
                    return sorted(total_photos_info, key=key_sort, reverse=True)

    @db_connect(table="MergingUser", method="insert")
    def users_search(self):
        """
        Поиск подходящих пользователей по данным self.user_info
        Декоратором данные заносятся в таблицу merging_user
        """
        year_now = dt.datetime.date(dt.datetime.now()).year
        year_birth = self.user_info['year_birth']
        city = self.user_info['city_id']
        sex = 1 if self.user_info['sex'] == 2 else 2
        age_from = year_now - year_birth - 1
        age_to = year_now - year_birth + 1
        fields = 'country,sex,city,bdate'
        users_search = []
        params_delta = {
            'city': city,
            'sex': sex,
            'age_from': age_from,
            'age_to': age_to,
            'fields': fields,
            'count': 10,
            'offset': self.search_offset
        }
        response = self.get_stability('users.search', params_delta)
        self.user_offset_set()  # записываем параметр self.search_offset в БД
        self.search_offset += 10
        if response and response['response']['items']:
            for item in response['response']['items']:
                user_id = item['id']
                if not self._users_lock(user_id) and not self.verify_in_black_list(user_id):
                    users_search.append({
                        'merging_user_id': user_id,
                        'city_id': None if 'city' not in item else item['city']['id'],
                        'sex': item['sex'],
                        'first_name': item['first_name'],
                        'last_name': item['last_name'],
                        'bdate': None if 'bdate' not in item else item['bdate'],
                        'url': rf"https://vk.com/id{user_id}"
                    })
        # если достигнута максимально допустимая выдача, то список будет пустой.
        # Это ограничение выдачи первых 1000 пользоватлей.
        # Чтобы обойти это, можно находить пользователей через другие методы, например сначала находить группы, а
        # а из них уже пользователей. Данный функционал пока не реализован. Для этого можно создать отдельные функции.
        # Поэтому пока обнуляем парметр self.search_offset, в т.ч. и в БД, чтобы не было ошибки.
        if not users_search:
            self.user_offset_clear_db()
            self.search_offset = 0
            return self.users_search()
        return users_search

    def _users_lock(self, user_id):
        """
        Получение информации о том закрытый или нет профиль пользователя
        :return: bool
        """
        params_delta = {'user_ids': user_id}
        response = self.get_stability('users.get', params_delta)
        if response and 'is_closed' in response['response'][0]:
            return response['response'][0]['is_closed']
        return True

    @db_connect(table="User", method="insert")
    def get_info_users(self):
        """
        Получение данных о пользователе по его id
        :return: словарь с данными по пользователю
        Декоратором данные заносятся в таблицу user
        """

        params_delta = {'user_ids': self.user_id, 'fields': 'country,city,bdate,sex'}
        response = self.get_stability('users.get', params_delta)
        if response:
            birth_info = self.get_birth_date(response)
            birth_date = birth_info[0]
            birth_year = birth_info[1]
            return {
                'user_id': self.user_id,
                'city_id': response['response'][0]['city']['id'],
                'sex': response['response'][0]['sex'],
                'first_name': response['response'][0]['first_name'],
                'last_name': response['response'][0]['last_name'],
                'bdate': birth_date,
                'year_birth': birth_year
            }

    @staticmethod
    def get_birth_date(res: dict):
        """
        Получение данных о возрасте пользователя
        :return: кортеж с датой: str и годом рождения: int
        """
        birth_date = None if 'bdate' not in res['response'][0] else res['response'][0]['bdate']
        birth_year = None
        if birth_date:
            birth_date = None if len(birth_date.split('.')) < 3 else birth_date
            birth_year = time.strptime(birth_date, "%d.%m.%Y").tm_year if birth_date else None
        return birth_date, birth_year

    @db_connect(table="User", method="update")
    def update_year_birth(self, age: int):
        """
        Обновление данных о годе рождения в словаре user_info на основании указанного возраста
        Декоратором данные обновляются в БД
        """
        year_now = dt.datetime.date(dt.datetime.now()).year
        birth_year = year_now - age
        self.user_info['year_birth'] = birth_year
        return birth_year


if __name__ == '__main__':
    test = VkSearch()
