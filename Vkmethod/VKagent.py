import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import time
from VkSearch import VkSearch
import os


def user_bot():
    with open(os.path.join(os.getcwd(), "token.txt"), encoding='utf-8') as file:
        token = [t.strip() for t in file.readlines()]
    vk_session = vk_api.VkApi(token=token[0])
    longpool = VkLongPoll(vk_session)
    users = []
    for event in longpool.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                msg = event.text.lower()
                user_id = event.user_id
                if user_id not in users:
                    exec(f"id_{user_id} = VkAgent({user_id})")
                    exec(f"id_{user_id}.msg = '{msg}'")
                    users.append(user_id)
                else:
                    exec(f"id_{user_id}.msg = '{msg}'")

                while True:
                    exec(f"id_{user_id}.result = id_{user_id}.handler_func()")
                    x = compile(f"id_{user_id}.result[4]", "test", "eval")
                    if eval(x):
                        break


class VkAgent(VkSearch):

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.vk_session = vk_api.VkApi(token=self.token_bot)
        self.longpool = VkLongPoll(self.vk_session)
        self.fav = {}
        self.result = [None, None, None, None, None, 1]

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
        user_info = self.result[0]
        enter_age = self.result[1]
        if enter_age and self.msg.isdigit():
            age = int(self.msg)
            self.update_year_birth(user_info, age)
            return [user_info, True, None, 0, False, 3]
        elif enter_age and not self.msg.isdigit():
            self.send_message("Введите верный возраст")
            return [user_info, True, None, 0, True, 2]
        else:
            return [user_info, True, None, 0, False, 3]

    def step_other_func(self):
        if self.msg == '♥':
            return self.get_favorite()
        if self.msg == '+♥':
            return self.add_favorite()
        user_info = self.result[0]
        search_flag = self.result[1]
        search_info = self.result[2]
        step = self.result[3]
        if search_flag:
            search_info = self.users_search(user_info)
            search_flag = False
            return [user_info, search_flag, search_info, step, False, None]
        else:
            step += 1
            value = list(search_info.values())[step]
            self.send_info_users(value)
            self.send_message("Выберите действие", buttons=['+♥', 'Далее', '♥'])
            if step == len(value) - 1:
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
        user_info = self.get_info_users()
        exit_flag = self.messages_var()
        if not user_info['year_birth'] and not exit_flag:  # После создания БД, проверку сделать по запросу из БД
            self.send_message("Укажите ваш возраст")
            enter_age = True
        return [user_info, enter_age, exit_flag, None, enter_age, 2]

    def send_message(self, some_text, button=False, buttons=False, title=''):
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
            if len(buttons) == 3:
                keyboard = VkKeyboard(inline=True)
                buttons_color = [VkKeyboardColor.SECONDARY, VkKeyboardColor.NEGATIVE, VkKeyboardColor.SECONDARY]
            for btn, btn_color in zip(buttons, buttons_color):
                keyboard.add_button(btn, btn_color)
            params['keyboard'] = keyboard.get_keyboard()
        try:
            self.vk_session.method("messages.send", params)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            self.send_message(some_text, button, title)

    def send_top_photos(self, user_id):
        """Отправка топ-3 фотографий пользователя"""
        self.send_message("Подождите, получаем топ-3 фото пользователя...")
        top_photo = self.top_photo(user_id)
        if not self._users_lock(user_id) and top_photo:
            attachment = ''
            for photo in top_photo:
                attachment += f"photo{user_id}_{photo[0]},"
            self.vk_session.method("messages.send", {
                "user_id": self.user_id,
                "attachment": attachment[:-1],
                "random_id": 0})
        elif top_photo:
            self.send_message("Извините, но у пользователя закрытый профиль.\n Вы можете посмотреть фото по ссылкам")
            for photo in top_photo:
                self.send_message(photo[1])
        else:
            self.send_message("Извините, но у пользователя нет доступных фотографий")

    def messages_var(self):
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

    def add_favorite(self):
        self.fav.update({self.result[6]['user_id']: self.result[6]})
        send_msg = f"Пользователь {self.result[6]['user_id']}:\n{self.result[6]['first_name']} {self.result[6]['last_name']} добавлен в избранное"
        self.send_message(send_msg)
        self.send_message("Выберите действие", buttons=['+♥', 'Далее', '♥'])
        return self.result

    def send_info_users(self, value):
        info = f"{value['first_name']} {value['last_name']}\n{value['url']}\n\n"
        self.send_message(info)
        self.send_top_photos(value['user_id'])

    def get_favorite(self):
        self.send_message("Вывожу избранных пользователей\n\n")
        for user_fav in self.fav.values():
            self.send_info_users(user_fav)
        self.send_message("-"*50)
        self.send_message("Выберите действие", buttons=['+♥', 'Далее', '♥'])
        return self.result


if __name__ == '__main__':
    user_bot()
