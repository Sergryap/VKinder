import urllib.parse
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from Date_base.created_table import User, Ses, OffsetUser, Photo
from Date_base.password import password


class DbMethods:
    """
    Класс методов взаимодействия с базой данных,
    не вошедших в декоратор db_connect
    """

    pswrd = urllib.parse.quote_plus(password)
    db = f"postgresql+psycopg2://sergryap:{pswrd}@localhost:5432/vkinder"
    engine = create_engine(db, echo=False)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)

    def get_favorite_db(self):
        """Получение данных об избранных пользователях для пользователя self.user_id"""
        sel = self.conn.execute(f"""
            SELECT
                merging_user.merging_user_id, merging_user.city_id,
                merging_user.sex, merging_user.first_name,
                merging_user.last_name, merging_user.bdate, merging_user.url
            FROM public.user
                JOIN public.user_merginguser USING (user_id)
                JOIN public.merging_user USING (merging_user_id)
            WHERE user_id = {self.user_id} and favorite = True 
            """).fetchall()
        return [{
            'merging_user_id': s[0],
            'city_id': s[1],
            'sex': s[2],
            'first_name': s[3],
            'last_name': s[4],
            'bdate': s[5],
            'url': s[6]
            }
            for s in sel
            ]

    def get_merging_user_db(self):
        """
        Получение информации о подходящих пользователях из merging_user
        для пользователя self.user_id
        """
        sel = self.conn.execute(f"""
            SELECT 
                merging_user.merging_user_id, merging_user.city_id,
                merging_user.sex, merging_user.first_name,
                merging_user.last_name, merging_user.bdate, merging_user.url
            FROM public.user
                JOIN public.user_merginguser USING (user_id)
                JOIN public.merging_user USING (merging_user_id)
            WHERE user_id = {self.user_id}
            ORDER BY merging_user_id
            OFFSET {self.offset_bd}
            LIMIT 10
            """).fetchall()

        self.offset_bd += 10
        merging_users = [{
            'merging_user_id': s[0],
            'city_id': s[1],
            'sex': s[2],
            'first_name': s[3],
            'last_name': s[4],
            'bdate': s[5],
            'url': s[6]
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
        при достижении в выводе последнего имеющегося в БД пользователя для self.user_id.
        Принята сортировка по id
        """

        end_merging_user = self.conn.execute(f"""
            SELECT 
                merging_user.merging_user_id
            FROM public.user
                JOIN public.user_merginguser USING (user_id)
                JOIN public.merging_user USING (merging_user_id)
            WHERE user_id = {self.user_id}
            ORDER BY merging_user_id DESC                    
            LIMIT 1
            """).fetchall()

        # end_merging_user = self.conn.execute(f"""
        #     SELECT merging_user_id
        #     FROM public.merging_user
        #     WHERE user_id = {self.user_id}
        #     ORDER BY merging_user_id DESC
        #     LIMIT 1
        #     """).fetchall()

        if end_merging_user[0][0] == end_sel:
            # обнуляем self.offset_bd, если дошли до последнего merging_users_id
            # и назначаем search_offset для продолжения поиска из VK
            self.search_offset = self.offset_bd - 10 + len_end_offset
            self.offset_bd = 0
            # меняем флаг, сигнализирующий о необходимости получать данные из БД
            self.merging_user_from_bd = False

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

    def user_offset_clear_db(self):
        """
        Удаление данных в таблице OffsetUser для пользователя self.user_id
        """
        session = self.Session()
        session.query(OffsetUser).filter(OffsetUser.user_id == self.user_id).delete()
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

    def verify_in_black_list(self, merging_user_id):
        """Проверка вхождения merging_user_id в стоп-лист"""
        sel = self.conn.execute(f"""
            SELECT merging_user_id
            FROM public.merging_user
                JOIN public.user_merginguser USING (merging_user_id)
            WHERE user_merginguser.user_id = {self.user_id}
                and merging_user.merging_user_id = {merging_user_id}
                and black_list = True
            """).fetchall()

        # sel = self.conn.execute(f"""
        #     SELECT merging_user_id
        #     FROM public.merging_user
        #     WHERE user_id = {self.user_id} and merging_user_id = {merging_user_id} and black_list = True
        #     """).fetchall()

        return bool(sel)
