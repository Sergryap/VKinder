import time
import urllib.parse
from datetime import date
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from Date_base.created_table import User, Ses, OffsetUser, MergingUser, Photo
from Date_base.password import password


class DBConnect:
    """Класс взаимодействия с базой данных"""

    pswrd = urllib.parse.quote_plus(password)
    db = f"postgresql+psycopg2://sergryap:{pswrd}@localhost:5432/vkinder"
    engine = create_engine(db, echo=False)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)

    def data_base_connector(self, table, method, data):
        """Функция для декоратора db_connect"""
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
        установкой значения атрибута favorite равным True в таблице MergingUser
        """
        session = self.Session()
        s = session.query(MergingUser).filter(MergingUser.merging_user_id == f_user_id and MergingUser.user_id == self.user_id)
        s.update({"favorite": True})
        session.commit()
        return self.result

    def get_favorite_db(self):
        """Получение данных об избранных пользователях для пользователя self.user_id"""
        sel = self.conn.execute(f"""
            SELECT *
            FROM public.merging_user
            WHERE user_id = {self.user_id} and favorite = True 
            """).fetchall()
        return [{
            'merging_user_id': s[0],
            'city_id': s[2],
            'sex': s[3],
            'first_name': s[4],
            'last_name': s[5],
            'bdate': s[6],
            'url': s[7]
            }
            for s in sel
            ]

    def get_merging_user_db(self):
        """
        Получение информации о подходящих пользователях из merging_user
        для пользователя self.user_id
        """
        sel = self.conn.execute(f"""
            SELECT *
            FROM public.merging_user
            WHERE user_id = {self.user_id} 
            ORDER BY merging_user_id
            OFFSET {self.offset_bd}
            LIMIT 10
            """).fetchall()
        self.offset_bd += 10
        merging_users = [{
            'merging_user_id': s[0],
            'city_id': s[2],
            'sex': s[3],
            'first_name': s[4],
            'last_name': s[5],
            'bdate': s[6],
            'url': s[7]
            }
            for s in sel
            ]
        end_users = merging_users[-1]['merging_user_id']
        len_merging_users = len(merging_users)
        # обнуляем self.offset_bd, если дошли до последнего merging_users_id
        self.set_offset_bd(end_users, len_merging_users)
        return merging_users

    def set_offset_bd(self, end_sel, len_end_offset):
        """
        Функция обнуления параметра self.offset_bd
        при достижении в выводе последнего имеющегося в БД пользователя.
        Принята сортировка по возрасту
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
        if birth_date:
            if len(birth_date.split(".")) == 3:
                date_info = time.strptime(birth_date, "%d.%m.%Y")
                year = date_info.tm_year
                month = date_info.tm_mon
                day = date_info.tm_mday
                month = month if month > 9 else str(f"0{month}")
                day = day if day > 9 else str(f"0{day}")
                return date.fromisoformat(f'{year}-{month}-{day}')

    def session_set(self):
        """Запись данных о сессии пользователя"""
        session = self.Session()
        ses_add = Ses(user_id=self.user_id, user_offset=self.search_offset, date_connect=date.today())
        session.add(ses_add)
        session.commit()

    def user_offset_get(self):
        """Получение параметра self.search_offset из БД"""
        sel = self.conn.execute(f"""
                    SELECT MAX(offset_user)
                    FROM public.offset_user
                    WHERE user_id = {self.user_id}                    
                    """).fetchone()
        if sel[0]:
            return sel[0]
        return 0

    def user_offset_set(self):
        """
        Запись параметра self.search_offset в БД
        Для использования при повторном подключении пользователя,
        чтобы не выводить повторно одних и тех же людей
        """
        session = self.Session()
        offset = 5 if self.search_offset == 0 else self.search_offset - 5
        offset_add = OffsetUser(user_id=self.user_id, offset_user=offset)
        session.add(offset_add)
        session.commit()

    def get_info_users_db(self):
        """
        Получение данных о пользователе self.user_id из БД
        """
        sel = self.conn.execute(f"""
                    SELECT *
                    FROM public.user
                    WHERE user_id = {self.user_id}
                """).fetchone()
        if sel:
            return {
                'user_id': sel[0],
                'city_id': sel[1],
                'sex': sel[2],
                'first_name': sel[3],
                'last_name': sel[4],
                'bdate': sel[5],
                'year_birth': sel[6]
            }

    def get_top_photo_db(self, merging_user_id):
        """
        Получение списка словарей, содержащих информацию о
        топ-3 фото пользователя merging_user_id
        """
        sel = self.conn.execute(f"""
                    SELECT *
                    FROM public.photo                                                
                    WHERE merging_user_id = {merging_user_id}
                """).fetchall()
        return [{
            'photo_id': s[0],
            'merging_user_id': s[1],
            'photo_url': s[2],
            'count_likes': s[3]
                }
                for s in sel]


def db_connect(table, method):
    """Декоратор для записи данных в БД"""

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
