import time
import urllib.parse
from datetime import date
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from Date_base.created_table import User, Ses, MergingUser, Photo


# from Date_base.password import password


class DBConnect():
    pswrd = urllib.parse.quote_plus('')
    db = f"postgresql+psycopg2://sergryap:{pswrd}@localhost:5432/vkinder"
    engine = create_engine(db, echo=False)
    conn = engine.connect()
    Session = sessionmaker(bind=engine)

    def data_base_connector(self, table, method, data):

        if method == "insert" and data:
            if table == "User":
                self.insert_db_table(data, table)
            elif table == "MergingUser":
                self.insert_db_table_list(data, table)
            elif table == "Photo":
                self.insert_db_table_photo(data, table)
        if method == "update":
            self.update_db_year_birth(data)
        if method == "delete":
            self.delete_data_table(table)

    def insert_db_table(self, data: dict, table: str):
        data['bdate'] = self.date_format(data['bdate'])
        if self.verify_insert_user():
            session = self.Session()
            user_add = eval(table)(**data)
            session.add(user_add)
            session.commit()

    def insert_db_table_list(self, data_users: list, table: str):
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
        session = self.Session()
        for photo in top_photo:
            if self.verify_insert_photo(photo["photo_id"]):
                photo_add = eval(table)(**photo)
                session.add(photo_add)
        session.commit()

    def verify_insert_user(self):
        sel = self.conn.execute(f"""
            SELECT user_id
            FROM public.user
            WHERE user_id = {self.user_id}
            """).fetchall()
        return not sel

    def verify_insert_merging_user(self, merging_user_id):
        sel = self.conn.execute(f"""
            SELECT merging_user_id
            FROM public.merging_user
            WHERE merging_user_id = {merging_user_id}
            """).fetchall()
        return not sel

    def verify_insert_photo(self, photo_id):
        sel = self.conn.execute(f"""
            SELECT photo_id
            FROM public.photo
            WHERE photo_id = '{photo_id}'
            """).fetchall()
        return not sel

    def update_db_year_birth(self, new_year):
        session = self.Session()
        session.query(User).filter(User.user_id == self.user_id).update({"year_birth": new_year})
        session.commit()

    def delete_data_table(self, table: str):
        session = self.Session()
        session.query(eval(table)).filter(User.user_id == self.user_id).delete()
        session.commit()

    @staticmethod
    def date_format(birth_date: str):
        if birth_date:
            date_info = time.strptime(birth_date, "%d.%m.%Y")
            year = date_info.tm_year
            month = date_info.tm_mon
            day = date_info.tm_mday
            month = month if month > 9 else str(f"0{month}")
            day = day if day > 9 else str(f"0{day}")
            return date.fromisoformat(f'{year}-{month}-{day}')


def db_connect(table, method):
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
    # print(x.verify_insert_photo("photo403915049_457239075"))
