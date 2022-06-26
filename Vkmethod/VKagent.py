import requests
import json
import os
from Token import token as token_bot
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import time
import datetime as dt
from pprint import pprint


class VkAgent:
	url = 'https://api.vk.com/method/'
	with open(os.path.join(os.getcwd(), "token.txt"), encoding='utf-8') as file:
		token = [t.strip() for t in file.readlines()]

	vk_session = vk_api.VkApi(token=token_bot)
	session_api = vk_session.get_api()
	longpool = VkLongPoll(vk_session)

	def __init__(self, tok=token[0]):
		self.params = {'access_token': tok, 'v': '5.131'}
		self.author = 0

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

	def get_message(self):
		enter_age = False
		for event in self.longpool.listen():
			if event.type == VkEventType.MESSAGE_NEW:
				if event.to_me:
					msg = event.text.lower()
					if not enter_age:
						user_info = self.msg_processing_not_enter_age(event, msg)
						enter_age = True
					if enter_age and msg.isdigit():
						age = int(msg)
						self.update_year_birth(user_info, age)
						# следует запись в БД
						enter_age = False
						pprint(user_info)

	def msg_processing_not_enter_age(self, event, msg):
		"""
		Обработка сообщения пользователя, когда не вводится возраст
		"""
		user_id = event.user_id
		user_info = self.set_search_users(user_id)
		# следует запись в БД
		pprint(user_info)
		self.messages_var(user_id, msg)
		if not user_info['year_birth']:  # При наличии БД, проверку сделать по запросу из БД
			self.send_message(user_id, "Укажите ваш возраст")
		return user_info

	@staticmethod
	def update_year_birth(user_info: dict, age: int):
		"""Обновление данных о годе рождения в словаре user_info на основании указанного возраста"""
		year_now = dt.datetime.date(dt.datetime.now()).year
		birth_year = year_now - age
		user_info['year_birth'] = birth_year

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

	def set_search_users(self, user_id):
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

	def send_message(self, user_id, some_text):
		self.vk_session.method("messages.send", {"user_id": user_id, "message": some_text, "random_id": 0})

	def messages_var(self, user_id, msg):
		if msg in ['да', 'конечно', 'yes', 'хочу']:
			return self.send_message(user_id, "Сейчас сделаю")
		if msg in ['нет', 'не надо', 'не хочу']:
			return self.send_message(user_id, "Очень жаль. Ждем в следующий раз")
		else:
			return self.send_message(user_id, "Я могу подобрать варианты знакомства для вас")


if __name__ == '__main__':
	bot_1 = VkAgent()
	bot_1.get_message()
