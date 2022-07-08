import requests
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import time
from Vkmethod.VkSearch import VkSearch
import os
from Date_base.DecorDB import db_connect


class VkAgent(VkSearch):
	"""
	Основной класс взаимодействия пользователя и бота
	"""

	def __init__(self, user_id):
		super().__init__()
		self.user_id = user_id
		self.vk_session = vk_api.VkApi(token=self.token_bot)
		self.search_flag = True  # флаг, указывающий на необходимость формирования временного списка к выдаче
		self.search_info = []  # хранит временный список подходящих пользователей к выдаче
		self.step = 0  # хранит индекс из списка подходящих пользователей к выводу из self.search_info
		self.user_info = []  # хранит данные о текущем пользователе, общающимся с ботом
		self.enter_age = None  # флаг о необходимости запроса возраста при недостатке данных о возрасте
		self.exit_flag = None  # флаг о нежелании пользователя продолжать общение
		self.step_handler_func = 1  # флаг о текущем шаге выполнения функции
		self.waiting_message = False    # флаг ожидания сообщения от пользователя
		self.current_user = {}  # хранит информацию о только что выведенном пользователе для занесения его в избранные в случае необходимости

	def handler_func(self):
		"""Функция-обработчик событий сервера типа MESSAGE_NEW"""
		if self.step_handler_func == 1:
			return self.get_data_user()
		if self.exit_flag in [2, 3]:
			self.exit_flag = None
			self.step_handler_func = 1
			self.waiting_message = True
			return None

		if self.step_handler_func == 2:
			return self.step_2_func()
		else:
			return self.step_other_func()

	def step_2_func(self):
		"""Функция-обработчик сообщения от пользователя после ввода возраста"""
		if self.enter_age and self.msg.isdigit():
			age = int(self.msg)
			self.update_year_birth(age)
			self.step_handler_func = 3
			self.waiting_message = False
			return None

		elif self.enter_age and not self.msg.isdigit():
			self.send_message("Введите верный возраст")
			# Если возраст введен не верно уходим на второй круг и т.д.
			self.step_handler_func = 2
			self.waiting_message = True
			return None

		else:
			self.step_handler_func = 3
			self.waiting_message = False
			return None

	def step_other_func(self):
		"""Функция-обработчик остальных сообщений пользователя"""
		if self.msg == '♥':
			return self.get_favorite()
		if self.msg == '+♥':
			return self.add_favorite()
		if self.msg == '✘ в стоп-лист':
			return self.add_black_list()
		if self.msg == 'с начала':
			return self.restart()
		if self.msg == 'очистить избранное':
			return self.favorite_clear()
		if self.search_flag:
			self.send_message("Немного подождите. Получаем данные...")
			if not self.merging_user_from_bd:
				self.search_info = self.users_search()
			else:
				self.search_info = self.get_merging_user_db()
			self.search_flag = False
			self.waiting_message = False
			return None

		else:
			self.current_user = self.search_info[self.step]
			self.step += 1
			self.send_info_users()
			self.waiting_message = True
			self.send_message("Выберите действие", buttons=self.number_buttons(2))
			if self.step == len(self.search_info):
				self.step = 0
				self.search_flag = True
			return None

	def get_data_user(self):
		"""
		Получение данных о пользователе при первом обращении к боту
		:return: словарь с данными о пользователе и флаг
		enter_age: bool, указывающий на необходимость запроса возраста
		"""
		self.enter_age = False
		self.user_info = self.get_info_users_db()
		self.user_info = self.get_info_users() if not self.user_info else self.user_info
		self.exit_flag = self.messages_var()
		if not self.user_info['year_birth'] and not self.exit_flag:
			self.send_message("Укажите ваш возраст")
			self.enter_age = True
		self.step_handler_func = 2
		self.waiting_message = self.enter_age
		return None

	def send_message(self, some_text, button=False, buttons=False, title=''):
		"""
		Отправка сообщения пользователю.
		В том числе, с созданием кнопок при необходимости
		"""
		params = {
			"user_id": self.user_id,
			"message": some_text,
			"random_id": 0}
		self.get_buttons(params, button, buttons, title)
		try:
			self.vk_session.method("messages.send", params)
		except requests.exceptions.ConnectionError:
			time.sleep(1)
			self.send_message(some_text, button, title)

	@staticmethod
	def get_buttons(params: dict, button, buttons, title):
		"""Создание кнопок для отправки команд"""
		if button:
			keyboard = VkKeyboard()
			keyboard.add_button(title, VkKeyboardColor.PRIMARY)
			params['keyboard'] = keyboard.get_keyboard()
		if buttons:
			if buttons[0] == 1:
				keyboard_1 = VkKeyboard(one_time=True)
				buttons_color = [VkKeyboardColor.SECONDARY, VkKeyboardColor.NEGATIVE]
				for btn, btn_color in zip(buttons[1], buttons_color):
					keyboard_1.add_button(btn, btn_color)
				params['keyboard'] = keyboard_1.get_keyboard()

			if buttons[0] == 2:
				keyboard_2 = VkKeyboard(inline=False)
				buttons_color = [
					VkKeyboardColor.SECONDARY,
					VkKeyboardColor.PRIMARY,
					VkKeyboardColor.SECONDARY,
					VkKeyboardColor.POSITIVE,
					VkKeyboardColor.NEGATIVE
				]
				for btn, btn_color in zip(buttons[1][:3], buttons_color[:3]):
					keyboard_2.add_button(btn, btn_color)
				keyboard_2.add_line()
				for btn, btn_color in zip(buttons[1][3:], buttons_color[3:]):
					keyboard_2.add_button(btn, btn_color)
				params['keyboard'] = keyboard_2.get_keyboard()

			if buttons[0] == 3:
				keyboard_3 = VkKeyboard(one_time=False, inline=True)
				keyboard_3.add_button(buttons[1], VkKeyboardColor.SECONDARY)
				params['keyboard'] = keyboard_3.get_keyboard()

	@staticmethod
	def number_buttons(n=1):
		if n == 1:
			return 1, ["Да", "Нет"]
		if n == 2:
			return 2, ['+♥', '>>>', '♥', 'С начала', '✘ в стоп-лист']
		if n == 3:
			return 3, 'Очистить избранное'

	def send_top_photos(self, merging_user_id):
		"""Отправка топ-3 фотографий пользователя"""
		self.send_message("Подождите, получаем топ-3 фото пользователя...")
		top_photo = self.get_top_photo_db(merging_user_id)
		if not top_photo:
			top_photo = self.top_photo(merging_user_id)
		if not self._users_lock(merging_user_id) and top_photo:
			attachment = ''
			for photo in top_photo:
				attachment += f"{photo['photo_id']},"
			self.vk_session.method("messages.send", {
				"user_id": self.user_id,
				"attachment": attachment[:-1],
				"random_id": 0})
		elif top_photo:
			self.send_message("Извините, но у пользователя закрытый профиль.\n Вы можете посмотреть фото по ссылкам")
			for photo in top_photo:
				self.send_message(photo['photo_url'])
		else:
			self.send_message("Извините, но у пользователя нет доступных фотографий")

	def messages_var(self):
		"""
		Обработка сообщений пользователя при первом обращении к боту
		"""
		if self.msg in ['да', 'конечно', 'yes', 'хочу', 'давай', 'буду']:
			self.send_message("Сейчас сделаю")
			return False
		if self.msg in ['нет', 'не надо', 'не хочу', 'потом']:
			self.send_message(
				"Очень жаль. Ждем в следующий раз.\n Вы все еще можете передумать: Да/Нет",
				buttons=self.number_buttons())
			return 2
		else:
			self.send_message("Подобрать варианты для знакомств? Да/Нет", buttons=self.number_buttons())
			return 3

	@db_connect(table="MergingUser", method="update", flag="favorite")
	def add_favorite(self):
		"""
		Добавление пользователя в избранные
		"""
		send_msg = f"Пользователь {self.current_user['merging_user_id']}:\n{self.current_user['first_name']} {self.current_user['last_name']} добавлен в избранное"
		self.send_message(send_msg)
		self.send_message("Выберите действие", buttons=self.number_buttons(2))
		return None

	@db_connect(table="MergingUser", method="update", flag="black")
	def add_black_list(self):
		"""
		Добавление пользователя в black_list
		"""
		send_msg = f"Пользователь {self.current_user['merging_user_id']}:\n{self.current_user['first_name']} {self.current_user['last_name']} добавлен в стоп-лист"
		self.send_message(send_msg)
		self.send_message("Выберите действие", buttons=self.number_buttons(2))
		return None

	def get_favorite(self):
		"""
		Вывод информации об избранных пользователях и отправка пользователю
		"""
		self.send_message("Избранные пользователи:\n")
		favorites = self.get_favorite_db()
		info_send = f'{"♥" * 10}\n'
		for user_fav in favorites:
			info_send += f"{user_fav['first_name']} {user_fav['last_name']} {user_fav['url']}\n"
		info_send += f'{"♥" * 10}\n'
		self.send_message(info_send)
		self.send_message("Выберите действие:", buttons=self.number_buttons(3))
		return None

	def favorite_clear(self):
		self.favorite_clear_db()
		self.send_message("Список избранных очищен.")
		self.send_message("Выберите действие", buttons=self.number_buttons(2))
		return None

	def restart(self):
		"""
		Установка параметров для начала обхода подходящих пользователей
		из имеющихся уже в БД
		"""
		self.search_flag = True
		self.search_info = None
		self.step = 0
		self.merging_user_from_bd = True
		self.send_message("Выберите действие", buttons=self.number_buttons(2))
		self.waiting_message = True
		return None

	def send_info_users(self):
		"""
		Отправка информации о следующем найденном пользователе
		"""
		info = f"{self.current_user['first_name']} {self.current_user['last_name']} {self.current_user['url']}\n"
		self.send_message(info)
		self.send_top_photos(self.current_user['merging_user_id'])


if __name__ == '__main__':
	user_bot()
