import urllib.parse
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Boolean, Table, PrimaryKeyConstraint
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
    merging_users = relationship('MergingUser', secondary='user_merginguser', cascade="all,delete")
    ses = relationship('Ses', cascade="all,delete", backref='user')
    offsets = relationship('OffsetUser', cascade="all,delete", backref='user')


class MergingUser(Base):
    __tablename__ = 'merging_user'

    merging_user_id = Column(Integer, primary_key=True)
    city_id = Column(Integer)
    sex = Column(Integer, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bdate = Column(Date)
    url = Column(String(300))
    # users = relationship('User', secondary='user_merginguser', cascade="all,delete")
    photos = relationship('Photo', cascade="all,delete", backref='merging_user')


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


class Photo(Base):
    __tablename__ = 'photo'

    photo_id = Column(String(50), primary_key=True)
    merging_user_id = Column(Integer, ForeignKey("merging_user.merging_user_id"), nullable=False)
    photo_url = Column(String(300))
    count_likes = Column(Integer)


user_merginguser = Table(
    'user_merginguser', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.user_id'), nullable=False),
    Column('merging_user_id', Integer, ForeignKey('merging_user.merging_user_id'), default=0, nullable=False),
    Column('favorite', Boolean, default=False),
    Column('black_list', Boolean, default=False),
    PrimaryKeyConstraint('user_id', 'merging_user_id', name='user_merginguser_pk')
)


def create_db():
    pswrd = urllib.parse.quote_plus(password)
    db = f"postgresql://sergryap:{pswrd}@localhost:5432/vkinder"
    engine = create_engine(db, echo=True)
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    create_db()
