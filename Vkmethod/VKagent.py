import requests
import json
import os
from Token import token as token_bot
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import time


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
		for event in self.longpool.listen():
			if event.type == VkEventType.MESSAGE_NEW:
				if event.to_me:
					msg = event.text.lower()
					id = event.user_id
					self.messages_var(id, msg)


	def send_message(self, id, some_text):
		self.vk_session.method("messages.send", {"user_id": id, "message": some_text, "random_id": 0})


	def messages_var(self, id, msg):
		if msg in ['да', 'конечно', 'yes', 'хочу']:
			return self.send_message(id, "Сейчас сделаю")
		if msg in ['нет', 'не надо', 'не хочу']:
			return self.send_message(id, "Очень жаль. Ждем в следующий раз")
		else:
			return self.send_message(id, "Я могу подобрать варианты знакомства для вас")


if __name__ == '__main__':
	bot_1 = VkAgent()
	bot_1.get_message()
