import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import time
from Vkmethod.VkSearch import VkSearch
from Vkmethod.VKagent import VkAgent
import os


def user_bot():
	"""
	Основная функция взаимодействия. Точка входа
	Будет не лишним реализовать многопоточность, чтобы паралельно обрабатывать нескольких пользователей.
	"""
	token = VkSearch.token_bot
	vk_session = vk_api.VkApi(token=token)
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
						exec(f"id_{user_id}.handler_func()")
						x = compile(f"id_{user_id}.waiting_message", "test", "eval")
						if eval(x):
							break
			if event.type == VkEventType.USER_OFFLINE:
				user_id = event.user_id
				exec(f"id_{user_id}.search_offset = id_{user_id}.user_offset_get()")
				exec(f"id_{user_id}.session_set()")
	except requests.exceptions.ReadTimeout:
		user_bot()


if __name__ == '__main__':
	user_bot()
