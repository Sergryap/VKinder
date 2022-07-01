import urllib.parse
from functools import wraps
import sqlalchemy.orm
from sqlalchemy import create_engine
from Date_base.password import password
from sqlalchemy import insert, values, update, delete, select
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.orm.query import Query
from Date_base.created_table import User, Ses, MergingUser, Photo
from Date_base.password import password


class DBConnect():
	pswrd = urllib.parse.quote_plus(password)
	db = f"postgresql+psycopg2://sergryap:{pswrd}@localhost:5432/vkinder"
	engine = create_engine(db, echo=True)
	Session = sessionmaker(bind=engine)

	def data_base_connector(self, table, method, result=None, attr=None, new_value=None):
		if method == "insert":
			self.insert_db(result)
		if method == "update":
			self.update_db(table, attr, new_value)
		if method == "delete":
			self.delete_db(table)

	def insert_db(self, data: dict):
		# query = Query([table], session=self.session)
		session = self.Session()
		user_add = User(**data)
		session.add(user_add)
		session.commit()


	def update_db(self, table, attr, new_value):
		x = compile(f"{attr}={new_value}", "test", "eval")
		s = update(table).where(user_id=self.user_id).values(eval(x))
		self.conn.execute(s)

	def delete_db(self, table):
		d = delete(table).where(user_id=self.user_id)
		self.conn.execute(d)

	def select_attr_db(self, table, attr):
		x = compile(f"{table}.{attr}", "test", "eval")
		s = select([eval(x)]).where(user_id=self.user_id)
		rs = self.conn.execute(s)
		return rs.fetchall()


def db_connect(table, method, attr=None, new_value=None):
	def dbase(old_func):
		@wraps(old_func)
		def new_func(self, *args, **kwargs):
			result = old_func(self, *args, **kwargs)
			DBConnect.data_base_connector(self, table, method, result, attr, new_value)
			return result

		return new_func

	return dbase


if __name__ == '__main__':
	x = DBConnect()
	x.insert_db({"user_id": 4545, "city_id": 110, "sex": 2, "first_name": "Сергей", "last_name": "Ряпин"})
