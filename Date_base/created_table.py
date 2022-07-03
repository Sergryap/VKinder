import urllib.parse
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Boolean, Table, MetaData, PrimaryKeyConstraint, schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from Date_base.password import password


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    city_id = Column(Integer)
    sex = Column(Integer, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bdate = Column(Date)
    year_birth = Column(Integer)
    merging_users = relationship('MergingUser', cascade="all,delete", backref='user')
    ses = relationship('Ses', cascade="all,delete", backref='user')
    offsets = relationship('OffsetUser', cascade="all,delete", backref='user')


class Ses(Base):
    __tablename__ = 'ses'

    session_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    user_offset = Column(Integer)
    date_connect = Column(Date)


class OffsetUser(Base):
    __tablename__ = 'offset_user'

    offset_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    offset_user = Column(Integer)


class MergingUser(Base):
    __tablename__ = 'merging_user'

    merging_user_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    city_id = Column(Integer)
    sex = Column(Integer, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bdate = Column(Date)
    url = Column(String(300))
    favorite = Column(Boolean, default=False)
    photos = relationship('Photo', cascade="all,delete", backref='merging_user')



class Photo(Base):
    __tablename__ = 'photo'

    photo_id = Column(String(50), primary_key=True)
    merging_user_id = Column(Integer, ForeignKey("merging_user.merging_user_id"), nullable=False)
    photo_url = Column(String(300))
    count_likes = Column(Integer)


def create_db():
    pswrd = urllib.parse.quote_plus(password)
    db = f"postgresql://sergryap:{pswrd}@localhost:5432/vkinder"
    engine = create_engine(db, echo=True)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    create_db()
