import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import time
from Vkmethod.VkSearch import VkSearch
import os
from Date_base.DecorDB import db_connect


def user_bot():
	"""Основная функция взаимодействия. Точка входа"""
	with open(os.path.join(os.getcwd(), "token.txt"), encoding='utf-8') as file:
		token = [t.strip() for t in file.readlines()]
	vk_session = vk_api.VkApi(token=token[0])
	try:
		longpool = VkLongPoll(vk_session)
		users = []
		for event in longpool.listen():
			if event.type == VkEventType.MESSAGE_NEW:
				if event.to_me:
					msg = event.text.lower()
					user_id = event.user_id
					if user_id not in users:
						# Для каждого пользователя создаем свой класс
						exec(f"id_{user_id} = VkAgent({user_id})")
						exec(f"id_{user_id}.msg = '{msg}'")
						# Устанавливаем значение self.search_offset из базы данных
						# Для уменьшения повторной выдачи тех же пользователей
						exec(f"id_{user_id}.search_offset = id_{user_id}.user_offset_get()")
						users.append(user_id)
					else:
						exec(f"id_{user_id}.msg = '{msg}'")
					while True:
						exec(f"id_{user_id}.result = id_{user_id}.handler_func()")
						x = compile(f"id_{user_id}.result[4]", "test", "eval")
						if eval(x):
							break
			if event.type == VkEventType.USER_OFFLINE:
				user_id = event.user_id
				exec(f"id_{user_id}.session_set()")
	except requests.exceptions.ReadTimeout:
		user_bot()


class VkAgent(VkSearch):

	def __init__(self, user_id):
		super().__init__()
		self.user_id = user_id
		self.vk_session = vk_api.VkApi(token=self.token_bot)
		self.longpool = VkLongPoll(self.vk_session)
		self.fav = []
		self.result = [None, None, None, None, None, 1]  # список для хранения временных данных и управляющих флагов
		# self.result[0] - хранит данные о текущем пользователе в чате
		# self.result[1] - при первом обращении заносится флаг о необходимости запроса возраста при недостатке данных
		# При последующих обращения хранит информацию о небходимости формирования временного списка подходящих пользователей
		# self.result[2] - хранит временный список подходящих пользователей
		# self.result[3] - хранит индекс из списка подходящих пользователей к выводу для self.user_id
		# self.result[4] - хранит флаг о необходимости прерывания цикла, в котором выполняется функция handler_func,
		# в случае ожидания сообщения от пользователя
		# self.result[5] - хранит флаг, указывающий на необходимость вызова функции обновления данных о возрасте,
		# после его указания пользователем
		# self.result[6] - индекс формируется по ходу выполнения и хранит информацию о только что
		# выведенном пользователе для занесения его в избранные в случае необходимости

	def handler_func(self):
		"""Функция-обработчик событий сервера типа MESSAGE_NEW"""
		if self.result[5] == 1:
			return self.get_data_user()
		if self.result[2] in [2, 3]:
			return [None, None, None, None, True, 1]
		if self.result[5] == 2:
			return self.step_2_func()
		else:
			return self.step_other_func()

	def step_2_func(self):
		"""Функция-обработчик сообщения от пользователя с указанным возрастом"""
		user_info = self.result[0]
		enter_age = self.result[1]
		if enter_age and self.msg.isdigit():
			age = int(self.msg)
			self.update_year_birth(user_info, age)
			return [user_info, True, None, 0, False, 3]
		elif enter_age and not self.msg.isdigit():
			self.send_message("Введите верный возраст")
			# Если возраст введен не верно уходим на второй круг и т.д.
			return [user_info, True, None, 0, True, 2]
		else:
			return [user_info, True, None, 0, False, 3]

	def step_other_func(self):
		"""Функция-обработчик остальных сообщений пользователя"""
		if self.msg == '♥':
			return self.get_favorite()
		if self.msg == '+♥':
			return self.add_favorite()
		if self.msg == 'с начала':
			return self.restart()
		user_info = self.result[0]
		search_flag = self.result[1]
		search_info = self.result[2]
		step = self.result[3]
		if search_flag:
			if not self.merging_user_from_bd:
				search_info = self.users_search(user_info)
			else:
				search_info = self.get_merging_user_db()
			search_flag = False
			return [user_info, search_flag, search_info, step, False, None]
		else:
			value = search_info[step]
			step += 1
			self.send_info_users(value)
			self.send_message("Выберите действие", buttons=['+♥', 'Далее', '♥', 'С начала'])
			if step == len(search_info):
				step = 0
				search_flag = True
			return [user_info, search_flag, search_info, step, True, None, value]

	def get_data_user(self):
		"""
		Получение данных о пользователе при первом обращении к боту
		:return: словарь с данными о пользователе и флаг
		enter_age: bool, указывающий на необходимость запроса возраста
		"""
		enter_age = False
		user_info = self.get_info_users_db()
		user_info = self.get_info_users() if not user_info else user_info
		exit_flag = self.messages_var()
		if not user_info['year_birth'] and not exit_flag:  # После создания БД, проверку сделать по запросу из БД
			self.send_message("Укажите ваш возраст")
			enter_age = True
		return [user_info, enter_age, exit_flag, None, enter_age, 2]

	def send_message(self, some_text, button=False, buttons=False, title=''):
		"""
		Отправка сообщения пользователю.
		В том числе, с созданием кнопок при необходимости
		"""
		params = {
			"user_id": self.user_id,
			"message": some_text,
			"random_id": 0}
		if button:
			keyboard = VkKeyboard()
			keyboard.add_button(title, VkKeyboardColor.PRIMARY)
			params['keyboard'] = keyboard.get_keyboard()
		if buttons:
			if len(buttons) == 2:
				keyboard = VkKeyboard(one_time=True)
				buttons_color = [VkKeyboardColor.SECONDARY, VkKeyboardColor.NEGATIVE]
			if len(buttons) == 4:
				keyboard = VkKeyboard(inline=True)
				buttons_color = [VkKeyboardColor.SECONDARY, VkKeyboardColor.NEGATIVE, VkKeyboardColor.SECONDARY,
				                 VkKeyboardColor.NEGATIVE]
			for btn, btn_color in zip(buttons, buttons_color):
				keyboard.add_button(btn, btn_color)
			params['keyboard'] = keyboard.get_keyboard()
		try:
			self.vk_session.method("messages.send", params)
		except requests.exceptions.ConnectionError:
			time.sleep(1)
			self.send_message(some_text, button, title)

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
			self.send_message("Очень жаль. Ждем в следующий раз.\n Вы все еще можете передумать: Да/Нет",
				buttons=["Да", "Нет"])
			return 2
		else:
			self.send_message("Подобрать варианты для знакомств? Да/Нет", buttons=["Да", "Нет"])
			return 3

	@db_connect(table="MergingUser", method="update")
	def add_favorite(self):
		"""
		Добавление пользователя в избранные
		"""
		# self.fav.append(self.result[6])
		send_msg = f"Пользователь {self.result[6]['merging_user_id']}:\n{self.result[6]['first_name']} {self.result[6]['last_name']} добавлен в избранное"
		self.send_message(send_msg)
		self.send_message("Выберите действие", buttons=['+♥', 'Далее', '♥', 'С начала'])
		return self.result

	def get_favorite(self):
		"""
		Вывод информации об избранных пользователях и отправка пользователю
		"""
		self.send_message("Избранные пользователи:\n")
		favorites = self.get_favorite_db()
		info_send = f'{"♥" * 20}\n'
		for user_fav in favorites:
			info_send += f"{user_fav['first_name']} {user_fav['last_name']} {user_fav['url']}\n"
		info_send += f'{"♥" * 20}\n'
		self.send_message(info_send)
		self.send_message("Выберите действие", buttons=['+♥', 'Далее', '♥', 'С начала'])
		return self.result

	def restart(self):
		"""
		Установка параметров для начала обхода подходящих пользователей
		из имеющихся уже в БД
		"""
		search_flag = True
		search_info = None
		step = 0
		user_info = self.result[0]
		self.merging_user_from_bd = True
		self.send_message("Выберите действие", buttons=['+♥', 'Далее', '♥', 'С начала'])
		return [user_info, search_flag, search_info, step, True, None]

	def send_info_users(self, value):
		"""
		Отправка информации о следующем найденном пользователе
		"""
		info = f"{value['first_name']} {value['last_name']} {value['url']}\n"
		self.send_message(info)
		self.send_top_photos(value['merging_user_id'])


if __name__ == '__main__':
	user_bot()
