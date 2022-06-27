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
		self.vk_session = vk_api.VkApi(token=self.token_bot)
		self.longpool = VkLongPoll(self.vk_session)

	def get_message(self):
		count = 1
		for event in self.longpool.listen():
			if event.type == VkEventType.MESSAGE_NEW:
				if event.to_me:
					msg = event.text.lower()
					user_id = event.user_id
					if count == 1:
						result = self.get_data_user(user_id, msg)
					else:
						while True:
							result = self.handler_func(user_id, msg, count, result)
							count += 1
							if result[4]:
								break
					count += 1

	def handler_func(self, user_id, msg, count, result=None):
		if count == 2:
			user_info = result[0]
			enter_age = result[1]
			exit_flag = result[2]
			if enter_age and msg.isdigit():
				age = int(msg)
				self.update_year_birth(user_info, age)
			return user_info, True, None, 0, False
		else:
			user_info = result[0]
			search_flag = result[1]
			search_info = result[2]
			step = result[3]
			if search_flag:
				search_info = self.users_search(user_info)
				search_flag = False
				return user_info, search_flag, search_info, step, False
			else:
				value = list(search_info.values())[step]
				info = f"{value['first_name']} {value['last_name']}\n{value['url']}\n\n"
				step += 1
				self.send_message(user_id, info)
				self.send_top_photos(value['user_id'], user_id)
				self.send_message(user_id, "Для продолжения поиска введите любой символ")
				if step == len(value) - 1:
					step = 0
					search_flag = True
				return user_info, search_flag, search_info, step, True

	def get_data_user(self, user_id, msg):
		"""
		Получение данных о пользователе при первом обращении к боту
		:return: словарь с данными о пользователе и флаг
		enter_age: bool, указывающий на необходимость запроса возраста
		"""
		enter_age = False
		user_info = self.get_info_users(user_id)
		exit_flag = self.messages_var(user_id, msg)
		if not user_info['year_birth']:  # После создания БД, проверку сделать по запросу из БД
			self.send_message(user_id, "Укажите ваш возраст")
			enter_age = True
		return user_info, enter_age, exit_flag

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
		self.send_message(owner_id, "Подождите, получаем топ-3 фото пользователя...")
		top_photo = self.top_photo(user_id)
		if not self._users_lock(user_id) and top_photo:
			attachment = ''
			for photo in top_photo:
				attachment += f"photo{user_id}_{photo[0]},"
			self.vk_session.method("messages.send", {"user_id": owner_id, "attachment": attachment[:-1],
			                                         "random_id": 0})
		elif top_photo:
			self.send_message(owner_id, "Извините, но у пользователя закрытый профиль.\n Вы можете посмотреть фото по ссылкам")
			for photo in top_photo:
				self.send_message(owner_id, photo[1])
		else:
			self.send_message(owner_id, "Извините, но у пользователя нет доступных фотографий")

	def messages_var(self, user_id, msg):
		if msg in ['да', 'конечно', 'yes', 'хочу', 'давай', 'буду']:
			self.send_message(user_id, "Сейчас сделаю")
		if msg in ['нет', 'не надо', 'не хочу', 'потом']:
			self.send_message(user_id, "Очень жаль. Ждем в следующий раз")
			return 1
		else:
			self.send_message(user_id, "Подобрать варианты для знакомств? Да/Нет")
			return 2


if __name__ == '__main__':
	bot_1 = VkAgent()
	bot_1.get_message()
