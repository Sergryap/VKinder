import requests
import json
import os
import datetime as dt
import time
from Date_base.DecorDB import DBConnect
from Date_base.DecorDB import db_connect


class VkSearch(DBConnect):
    """
    Класс методов поиска и сортировки
    """
    url = 'https://api.vk.com/method/'

    def __init__(self):
        super().__init__()
        with open(os.path.join(os.getcwd(), "token.txt"), encoding='utf-8') as file:
            token = [t.strip() for t in file.readlines()]
        self.token_bot = token[0]
        self.token = token[1:]
        self.params = {'access_token': self.token[0], 'v': '5.131'}
        self.author = 0
        self.search_offset = 0

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
        count = i + 1
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

    @staticmethod
    def __get_items(item: dict):
        """
        Находим фото с наибольшим разрешением.
        Если данных по размерам нет, то принимаем по size['type']
        по данным словаря item
        """
        area = 0
        for size in item['sizes']:
            if size['height'] and size['width'] and size['height'] > 0 and size['width'] > 0:
                if size['height'] * size['width'] > area:
                    area = size['height'] * size['width']
                    photo_url = size['url']
            else:
                flag = False
                for i in 'wzyx':
                    for size1 in item['sizes']:
                        if size1['type'] == i:
                            photo_url = size1['url']
                            flag = True
                            break
                    if flag:
                        break
                break
        return photo_url

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
                photo_url = self.__get_items(item)
                likes = item['likes']['count']
                count_likes = str(likes)
                # Добавляем словарь в список photos_info
                photos_info.append({
                    'photo_url': photo_url,
                    'count_likes': count_likes,
                    'photo_id': item['id']
                })
            return photos_info

    def top_photo(self, owner_id):
        """
        Поиск топ-3 фото пользователя по всем альбомам пользователя
        """

        def key_sort(elem):
            return elem['count_likes']

        total_photos_info = []
        albums = self.__albums_id(owner_id)
        if albums:
            for album_id in albums:
                total_photos_info += self.__photos_get(owner_id, album_id)
                photos_sorted = sorted(total_photos_info, key=key_sort, reverse=True)[:3]
                return [(f['photo_id'], f['photo_url']) for f in photos_sorted]

    def users_search(self, users_info):
        """Поиск подходящих пользователей по данным users_info"""
        year_now = dt.datetime.date(dt.datetime.now()).year
        year_birth = users_info['year_birth']
        city = users_info['city_id']
        sex = 1 if users_info['sex'] == 2 else 2
        age_from = year_now - year_birth - 1
        age_to = year_now - year_birth + 1
        fields = 'country,sex,city,bdate'
        users_search = {}
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
        self.search_offset += 10
        if response and response['response']['items']:
            for item in response['response']['items']:
                user_id = item['id']
                users_search[user_id] = {
                    'user_id': user_id,
                    'city_id': None if 'city' not in item else item['city']['id'],
                    'sex': item['sex'],
                    'first_name': item['first_name'],
                    'last_name': item['last_name'],
                    'bdate': None if 'bdate' not in item else item['bdate'],
                    'url': rf"https://vk.com/id{user_id}"
                }
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

    # @db_connect(table="user", method="insert")
    def get_info_users(self):
        """
        Получение данных о пользователе по его id
        :return: словарь с данными по пользователю
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

    @staticmethod
    def update_year_birth(user_info: dict, age: int):
        """Обновление данных о годе рождения в словаре user_info на основании указанного возраста"""
        year_now = dt.datetime.date(dt.datetime.now()).year
        birth_year = year_now - age
        user_info['year_birth'] = birth_year


if __name__ == '__main__':
    serg = VkSearch()
    print(serg.top_photo(51166388))
