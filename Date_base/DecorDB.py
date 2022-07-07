import time
from datetime import date
from functools import wraps
from Date_base.created_table import User, Ses, OffsetUser, MergingUser, Photo
from Date_base.methodsDB import DbMethods


class DBConnect(DbMethods):
    """
    Класс методов для декоратора db_connect
    Декоратор реализует взаимодейстие между результатом функции и базой данных
    """

    def data_base_connector(self, table, method, data, flag):
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
                self.add_favorite_black(data[6]["merging_user_id"], flag=flag)
        if method == "delete":
            self.delete_data_table(table)

    def insert_db_table(self, data: dict, table: str):
        """Вставка одной строки в таблицу User"""
        if self.verify_insert_user():
            data['bdate'] = self.date_format(data['bdate'])
            session = self.Session()
            user_add = eval(table)(**data)
            session.add(user_add)
            session.commit()

    def insert_db_table_list(self, data_users: list, table: str):
        """Вставка нескольких строк в таблицу MergingUser"""
        values_1 = ''
        values_2 = ''

        for user in data_users:
            merging_user_id = user['merging_user_id']
            user['bdate'] = self.date_format(user['bdate'])
            if self.verify_insert_merging_user(merging_user_id):
                user['city_id'] = 0 if not user['city_id'] else user['city_id']
                values_1 += f"""
                    ({merging_user_id}, {user['city_id']}, {user['sex']},
                     '{user['first_name']}', '{user['last_name']}', '{user['bdate']}', '{user['url']}'),\n"""
                values_2 += f"({self.user_id}, {merging_user_id}, False, False),\n"

        if values_2:
            self.conn.execute(f"""
                INSERT INTO public.merging_user
                VALUES {values_1[:-2]}""")
            self.conn.execute(f"""
            INSERT INTO public.user_merginguser
            VALUES {values_2[:-2]}
            """)

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

    def add_favorite_black(self, f_user_id, flag="favorite"):
        """
        Добавление пользователя в стоп-лист либо в избранное
        установкой флага black_list равным True
        или favorite равным True в таблице user_merginguser
        """
        if flag == "favorite":
            f1, f2 = True, False
        elif flag == "black":
            f1, f2 = False, True

        self.conn.execute(f"""
        UPDATE public.user_merginguser
        SET favorite = {f1}, black_list = {f2}
        WHERE merging_user_id = {f_user_id} and user_id = {self.user_id}    
        """)
        return self.result

    def favorite_clear_db(self):
        """Очистка списка избранных и стоп-листа для пользователя self.user_id"""
        self.conn.execute(f"""
        UPDATE public.user_merginguser
        SET favorite = False, black_list = False
        WHERE user_id = {self.user_id}    
        """)

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


def db_connect(table, method, flag=None):
    """Декоратор для взаимодействия с базой данных"""

    def dbase(old_func):
        @wraps(old_func)
        def new_func(self, *args, **kwargs):
            result = old_func(self, *args, **kwargs)
            DBConnect.data_base_connector(self, table=table, method=method, data=result, flag=flag)
            return result

        return new_func

    return dbase


if __name__ == '__main__':
    x = DBConnect()
