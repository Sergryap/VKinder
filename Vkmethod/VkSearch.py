import requests
import json
import os


class VkSearch:
	url = 'https://api.vk.com/method/'
	with open(os.path.join(os.getcwd(), "token.txt"), encoding='utf-8') as file:
		token = [t.strip() for t in file.readlines()]

	def __init__(self, tok=token[0]):
		self.params = {'access_token': tok, 'v': '5.131'}
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
		Cоздает список словарей, содержащих название и id
		альбомы пользователя
		"""
		params_delta = {'owner_id': owner_id, 'need_system': '1'}
		response = self.get_stability('photos.getAlbums', params_delta)
		if response:
			albums_id = []
			for item in response['response']['items']:
				albums_id.append({
					'title': self._path_normalizer(item['title']),
					'id': item['id']
				})
			return albums_id
		return -1, -1

	@staticmethod
	def _path_normalizer(name_path):
		"""Удаление и замена запрещенных и нежелательных символов в имени папки"""
		symbol_no = rf"""*:'"%!@?$/\\|&<>+.)("""
		name = '_'.join(name_path.split()).strip(symbol_no)
		for s in symbol_no:
			if s in name:
				name = name.replace(s, '_')
		return name

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
					image_res = f"{size['height']} * {size['width']}"
					photo_url = size['url']
			else:
				flag = False
				for i in 'wzyx':
					for size1 in item['sizes']:
						if size1['type'] == i:
							image_res = "нет данных"
							photo_url = size1['url']
							flag = True
							break
					if flag:
						break
				break
		return image_res, photo_url

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
				photo_url = self.__get_items(item)[1]
				likes = item['likes']['count']
				count_likes = str(likes)
				# Добавляем словарь в список photos_info
				photos_info.append({
					'photo_url': photo_url,
					'count_likes': count_likes
				})
		return photos_info

	def photo_search(self, owner_id):
		"""
		Поиск топ-3 фото пользователя по всем альбомам пользователя
		"""
		def key_sort(elem):
			return elem['count_likes']

		total_photos_info = []
		for album_id in self.__albums_id(owner_id):
			total_photos_info += self.__photos_get(owner_id, album_id['id'])
		photos_sorted = sorted(total_photos_info, key=key_sort, reverse=True)[:2]
		return [f['photo_url'] for f in photos_sorted]

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

	def set_info_users(self, user_id):
		"""
		Получение данных о пользователе по его id
		:return: словарь с данными по пользователю
		"""
		params_delta = {'user_ids': user_id, 'fields': 'country,city,bdate,sex'}
		response = self.get_stability('users.get', params_delta)
		if response:
			birth_info = self.get_birth_date(response)
			birth_date = birth_info[0]
			birth_year = birth_info[1]
			return {
				'user_id': user_id,
				'city_id': response['response'][0]['city']['id'],
				'sex': response['response'][0]['sex'],
				'first_name': response['response'][0]['first_name'],
				'last_name': response['response'][0]['last_name'],
				'bdate': birth_date,
				'year_birth': birth_year
			}
