import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import time
from VkSearch import VkSearch


class VkAgent(VkSearch):

    def __init__(self):
        super().__init__()
        self.vk_session = vk_api.VkApi(token=self.token_bot)
        self.longpool = VkLongPoll(self.vk_session)

    def get_message(self):
        result = None, None, None, None, None, 1
        for event in self.longpool.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    msg = event.text.lower()
                    user_id = event.user_id
                    while True:
                        result = self.handler_func(user_id, msg, result)
                        if result[4]:
                            break

    def handler_func(self, user_id, msg, result):
        """Функция-обработчик событий сервера типа MESSAGE_NEW"""
        if result[5] == 1:
            return self.get_data_user(user_id, msg)
        if result[2] in [2, 3]:
            return None, None, None, None, True, 1
        if result[5] == 2:
            return self.step_2_func(result, msg, user_id)
        else:
            return self.step_other_func(result, user_id)

    def step_2_func(self, result, msg, user_id):
        user_info = result[0]
        enter_age = result[1]
        if enter_age and msg.isdigit():
            age = int(msg)
            self.update_year_birth(user_info, age)
            return user_info, True, None, 0, False, 3
        elif enter_age and not msg.isdigit():
            self.send_message(user_id, "Введите верный возраст")
            return user_info, True, None, 0, True, 2
        else:
            return user_info, True, None, 0, False, 3

    def step_other_func(self, result, user_id):
        user_info = result[0]
        search_flag = result[1]
        search_info = result[2]
        step = result[3]
        if search_flag:
            search_info = self.users_search(user_info)
            search_flag = False
            return user_info, search_flag, search_info, step, False, None
        else:
            value = list(search_info.values())[step]
            info = f"{value['first_name']} {value['last_name']}\n{value['url']}\n\n"
            step += 1
            self.send_message(user_id, info)
            self.send_top_photos(value['user_id'], user_id)
            self.send_message(user_id, "Для продолжения нажмите далее", button=True, title='Далее')
            if step == len(value) - 1:
                step = 0
                search_flag = True
            return user_info, search_flag, search_info, step, True, None

    def get_data_user(self, user_id, msg):
        """
        Получение данных о пользователе при первом обращении к боту
        :return: словарь с данными о пользователе и флаг
        enter_age: bool, указывающий на необходимость запроса возраста
        """
        enter_age = False
        user_info = self.get_info_users(user_id)
        exit_flag = self.messages_var(user_id, msg)
        if not user_info['year_birth'] and not exit_flag:  # После создания БД, проверку сделать по запросу из БД
            self.send_message(user_id, "Укажите ваш возраст")
            enter_age = True
        return user_info, enter_age, exit_flag, None, enter_age, 2

    def send_message(self, user_id, some_text, button=False, buttons=False, title=''):
        params = {
            "user_id": user_id,
            "message": some_text,
            "random_id": 0}
        if button:
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button(title, VkKeyboardColor.PRIMARY)
            params['keyboard'] = keyboard.get_keyboard()
        if buttons:
            keyboard = VkKeyboard(one_time=True)
            buttons_color = [VkKeyboardColor.PRIMARY, VkKeyboardColor.NEGATIVE]
            for btn, btn_color in zip(buttons, buttons_color):
                keyboard.add_button(btn, btn_color)
            params['keyboard'] = keyboard.get_keyboard()
        try:
            self.vk_session.method("messages.send", params)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            self.send_message(user_id, some_text, button, title)

    def send_top_photos(self, user_id, owner_id):
        """Отправка топ-3 фотографий пользователя"""
        self.send_message(owner_id, "Подождите, получаем топ-3 фото пользователя...")
        top_photo = self.top_photo(user_id)
        if not self._users_lock(user_id) and top_photo:
            attachment = ''
            for photo in top_photo:
                attachment += f"photo{user_id}_{photo[0]},"
            self.vk_session.method("messages.send", {
                "user_id": owner_id,
                "attachment": attachment[:-1],
                "random_id": 0})
        elif top_photo:
            self.send_message(owner_id,
                              "Извините, но у пользователя закрытый профиль.\n Вы можете посмотреть фото по ссылкам")
            for photo in top_photo:
                self.send_message(owner_id, photo[1])
        else:
            self.send_message(owner_id, "Извините, но у пользователя нет доступных фотографий")

    def messages_var(self, user_id, msg):
        if msg in ['да', 'конечно', 'yes', 'хочу', 'давай', 'буду']:
            self.send_message(user_id, "Сейчас сделаю")
            return False
        if msg in ['нет', 'не надо', 'не хочу', 'потом']:
            self.send_message(user_id, "Очень жаль. Ждем в следующий раз.\n Вы все еще можете передумать: Да/Нет",
                              buttons=["Да", "Нет"])
            return 2
        else:
            self.send_message(user_id, "Подобрать варианты для знакомств? Да/Нет", buttons=["Да", "Нет"])
            return 3


if __name__ == '__main__':
    bot_1 = VkAgent()
    bot_1.get_message()
