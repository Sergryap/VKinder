from unicodedata import name
from sqlalchemy import Column, Integer, String, ForeignKey, Table, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
# from sqlalchemy.dialects import postgresql -> у меня без этого не работал оставлю пока на всякий случай
import urllib.parse

Base = declarative_base()


class User(Base):
    __tablename__ = 'User'

    user_id = Column(Integer, primary_key=True)

    last_name = Column(String)
    first_name = Column(String)
    city = Column(String)
    bdate = Column(Integer)
    year_birth = Column(Integer)
    sex = Column(String)
    mergingusers = relationship('MergingUsers', backref='User')


class MergingUsers(Base):
    __tablename__ = 'MergingUsers'

    merging_id = Column(Integer, primary_key=True)
    last_name = Column(String)
    first_name = Column(String)
    sex = Column(String)
    photos = relationship('Photos', backref='MergingUsers')
    id_user = Column(Integer, ForeignKey('User.user_id'))


class Photos(Base):
    __tablename__ = 'Photos'

    photo_id = Column(Integer, primary_key=True)
    id_photo = Column(Integer, ForeignKey('MergingUsers.merging_id'))
    photo_url = Column(String)
    count_likes = Column(Integer)


# photo_user = Table(
#     'photo_user', Base.metadata,
#     Column('photo_id', Integer, ForeignKey('Photos.photo_id')),
#     Column('merging_id', Integer, ForeignKey('MergingUsers.merging_id')),
#     PrimaryKeyConstraint('photo_id', 'merging_id',
#                          name='photos_merging_users'))

# Тут решил добавить избранные и черный список тут еще в плане тестов

# class Favorites(Base):
#     __tablename__ = 'Favorites'

#     favorites_id = Column(Integer, primary_key = True)
#     last_name = Column(String)
#     first_name = Column(String)
#     id_user = Column(Integer, ForeignKey('User.user_id'))

# class BlackList(Base):
#     __tablename__ = 'BlackList'

#     black_list_id = Column(Integer, primary_key = True)
#     last_name = Column(String)
#     first_name = Column(String)
#     id_user = Column(Integer, ForeignKey('User.user_id'))

if __name__ == '__main__':
    password = urllib.parse.quote_plus('admin')
    db = f"postgresql://admin_vk:{password}@localhost:5432/admin"
    engine = create_engine(db, echo=True)
    Base.metadata.create_all(engine)
