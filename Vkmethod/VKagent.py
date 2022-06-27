import requests
import json
import os
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import time
import datetime as dt
from pprint import pprint
from VkSearch import VkSearch


class VkAgent(VkSearch):

	def __init__(self):
		super().__init__()
		self.vk_session = vk_api.VkApi(token=self.token[0])
		self.longpool = VkLongPoll(self.vk_session)

	def get_message(self):
		enter_age = False
		user_info = None
		users_search = {}
		search_flag = True
		step = 0
		for event in self.longpool.listen():
			if event.type == VkEventType.MESSAGE_NEW:
				if event.to_me:
					msg = event.text.lower()
					user_id = event.user_id
					if not enter_age and not user_info:
						# получение данных о пользователе первый раз
						# при отсутствии данных о возрасте enter_age будет True
						result = self.msg_processing_not_enter_age(event, msg)
						user_info = result[0]
						enter_age = result[1]
					if enter_age and msg.isdigit():
						# обновление данных после указания возраста пользователем
						age = int(msg)
						self.update_year_birth(user_info, age)
						enter_age = False
					if user_info['year_birth'] and search_flag:
						# поиск подходящих пользоватлей для пользователя из чата
						search_info = self.users_search(user_info)
						users_search.update(search_info)  # вместо этого будет дозапись в базу данных
						search_flag = False
						# здесь будет запись в базу данных из словарей user_info и users_search
						pprint(users_search)
					if not search_flag:
						value = list(search_info.values())[step]
						info = f"{value['first_name']} {value['last_name']}\n{value['url']}\n\n"
						step += 1
						self.send_message(user_id, info)
						self.send_top_photos(value['user_id'], user_id)
						self.send_message(user_id, "Для продолжения поиска введите любой символ")
						if step == len(value) - 1:
							step = 0
							search_flag = True

	def msg_processing_not_enter_age(self, event, msg):
		"""
		Обработка сообщения пользователя, когда не вводится возраст
		:return: словарь с данными о пользователе и
		enter_age: bool, указывающее на необходимость ввода возраста при следующей иттерации
		"""
		user_id = event.user_id
		enter_age = False
		user_info = self.set_info_users(user_id)
		self.messages_var(user_id, msg)
		if not user_info['year_birth']:  # После создания БД, проверку сделать по запросу из БД
			self.send_message(user_id, "Укажите ваш возраст")
			enter_age = True
		return user_info, enter_age

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

	def send_message(self, user_id, some_text):
		try:
			self.vk_session.method("messages.send", {"user_id": user_id, "message": some_text, "random_id": 0})
		except requests.exceptions.ConnectionError:
			time.sleep(1)
			self.send_message(user_id, some_text)

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

	def send_top_photos(self, user_id, owner_id):
		"""Отправка топ-3 фотографий пользователя"""
		self.send_message(owner_id, "Подождите, получаем топ-3 фото пользователя")
		top_photo = self.top_photo(user_id)
		if not self._users_lock(user_id) and top_photo:
			attachment = ''
			for photo in top_photo:
				attachment += f"photo{user_id}_{photo[0]},"
			self.vk_session.method("messages.send", {"user_id": owner_id, "attachment": attachment[:-1], "random_id": 0})
		elif top_photo:
			self.send_message(owner_id, "Извините, но у пользователя закрытый профиль.\n Вы можете посмотреть фото по ссылкам")
			for photo in top_photo:
				self.send_message(owner_id, photo[1])
		else:
			self.send_message(owner_id, "Извините, но у пользователя нет доступных фотографий")

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
