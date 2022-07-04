import time
import urllib.parse
from datetime import date
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from Date_base.created_table import User, Ses, OffsetUser, MergingUser, Photo
from Date_base.password import password
from Date_base.methodsDB import DbMethods


class DBConnect(DbMethods):
    """
    Класс методов для декоратора db_connect
    Декоратор реализует взаимодейстие между результатом функции и базой данных
    """

    def data_base_connector(self, table, method, data):
        """Основная внутренняя функция декоратора db_connect"""
        if method == "insert" and data:
            if table == "User":
                self.insert_db_table(data, table)
            elif table == "MergingUser":
                self.insert_db_table_list(data, table)
            elif table == "Photo":
                self.insert_db_table_photo(data, table)
        if method == "update":
            if table == "User":
                self.update_db_year_birth(data)
            elif table == "MergingUser":
                self.add_favorite_db(data[6]["merging_user_id"])
        if method == "delete":
            self.delete_data_table(table)

    def insert_db_table(self, data: dict, table: str):
        """Вставка одной строки в таблицу"""
        data['bdate'] = self.date_format(data['bdate'])
        if self.verify_insert_user():
            session = self.Session()
            user_add = eval(table)(**data)
            session.add(user_add)
            session.commit()

    def insert_db_table_list(self, data_users: list, table: str):
        """Вставка нескольких строк в таблицу"""
        session = self.Session()
        for user in data_users:
            user['bdate'] = self.date_format(user['bdate'])
            user['user_id'] = self.user_id
            merging_user_id = user['merging_user_id']
            if self.verify_insert_merging_user(merging_user_id):
                user_add = eval(table)(**user)
                session.add(user_add)
        session.commit()

    def insert_db_table_photo(self, top_photo: list, table: str):
        """Вставка информации о топ-фото для пользователя в отдельную таблицу"""
        session = self.Session()
        for photo in top_photo:
            if self.verify_insert_photo(photo["photo_id"]):
                photo_add = eval(table)(**photo)
                session.add(photo_add)
        session.commit()

    def verify_insert_user(self):
        """Проверка вхождения пользователя в таблицу User"""

        sel = self.conn.execute(f"""
            SELECT user_id
            FROM public.user
            WHERE user_id = {self.user_id}
            """).fetchall()
        return not sel

    def verify_insert_merging_user(self, merging_user_id):
        """проверка вхождения пользователя в таблицу MergingUser"""
        sel = self.conn.execute(f"""
            SELECT merging_user_id
            FROM public.merging_user
            WHERE merging_user_id = {merging_user_id}
            """).fetchall()
        return not sel

    def verify_insert_photo(self, photo_id):
        """Проверка вхождения photo_id в таблицу Photo"""
        sel = self.conn.execute(f"""
            SELECT photo_id
            FROM public.photo
            WHERE photo_id = '{photo_id}'
            """).fetchall()
        return not sel

    def update_db_year_birth(self, new_year):
        """Обновление года рождения для пользователе self.user_id"""
        session = self.Session()
        session.query(User).filter(User.user_id == self.user_id).update({"year_birth": new_year})
        session.commit()

    def add_favorite_db(self, f_user_id):
        """
        Добавление пользователя в избранное
        установкой флага favorite равным True в таблице MergingUser
        """
        session = self.Session()
        s = session.query(MergingUser).filter(MergingUser.merging_user_id == f_user_id and MergingUser.user_id == self.user_id)
        s.update({"favorite": True})
        session.commit()
        return self.result

    def set_offset_bd(self, end_sel, len_end_offset):
        """
        Функция обнуления параметра self.offset_bd
        при достижении в выводе последнего имеющегося в БД пользователя.
        Принята сортировка по id
        """
        end_merging_user = self.conn.execute(f"""
            SELECT merging_user_id
            FROM public.merging_user
            WHERE user_id = {self.user_id} 
            ORDER BY merging_user_id DESC
            LIMIT 1
            """).fetchall()
        if end_merging_user[0][0] == end_sel:
            # обнуляем self.offset_bd, если дошли до последнего merging_users_id
            # и назначаем search_offset для продолжения поиска из VK
            self.search_offset = self.offset_bd - 10 + len_end_offset
            self.offset_bd = 0
            # меняем флаг, сигнализирующий о необходимости получать данные из БД
            self.merging_user_from_bd = False

    def delete_data_table(self, table: str):
        """Удаление данных из таблицы для пользователя self.user_id"""
        session = self.Session()
        session.query(eval(table)).filter(User.user_id == self.user_id).delete()
        session.commit()

    @staticmethod
    def date_format(birth_date: str):
        """Запись даты в формате fromisoformat"""
        if birth_date:
            if len(birth_date.split(".")) == 3:
                date_info = time.strptime(birth_date, "%d.%m.%Y")
                year = date_info.tm_year
                month = date_info.tm_mon
                day = date_info.tm_mday
                month = month if month > 9 else str(f"0{month}")
                day = day if day > 9 else str(f"0{day}")
                return date.fromisoformat(f'{year}-{month}-{day}')


def db_connect(table, method):
    """Декоратор для взаимодействия с базой данных"""

    def dbase(old_func):
        @wraps(old_func)
        def new_func(self, *args, **kwargs):
            result = old_func(self, *args, **kwargs)
            DBConnect.data_base_connector(self, table, method, result)
            return result

        return new_func

    return dbase


if __name__ == '__main__':
    x = DBConnect()
