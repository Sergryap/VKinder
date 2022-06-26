import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class MergingUsers(Base):
    __tablename__ = 'society_user'
    user_id_from = sq.Column(sq.Integer,
                             sq.ForeignKey('user.id'),
                             primary_key=True)
    user_id_to = sq.Column(sq.Integer,
                           sq.ForeignKey('user.id'),
                           primary_key=True)
    is_favorite = sq.Column(sq.Boolean, default=False)
    is_viewed = sq.Column(sq.Boolean, default=False)


class Users(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    params = relationship('SearchParams', uselist=False, backref='user')
    user_to = relationship('SocietyUser',
                           backref='to',
                           primaryjoin=id == MergingUsers.user_id_from)
    user_from = relationship('SocietyUser',
                             backref='from',
                             primaryjoin=id == MergingUsers.user_id_to)


class SearchParams(Base):
    __tablename__ = 'search_params'
    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.id'))
    b_year = sq.Column(sq.Integer)
    city = sq.Column(sq.String)
    status = sq.Column(sq.Integer)
    gender = sq.Column(sq.String)


association_user = sq.Table(
    'association_user', Base.metadata,
    sq.Column('user_id_to',
              sq.Integer,
              sq.ForeignKey('user.id'),
              primary_key=True),
    sq.Column('user_id_from',
              sq.Integer,
              sq.ForeignKey('user.id'),
              primary_key=True))
