import sqlalchemy as sqa
from sqlalchemy.orm import Session

from DB_model_table import Base, MergingUsers, Users, SearchParams


class VkDB:
    session = None
    engine = None
    Base = Base

    def __init__(self, connect):
        self.engine = sqa.create_engine(connect)
        self.session = Session(bind=self.engine)

    def db_init(self):
        self.Base.metadata.create_all(self.engine)
        print(f'DB created!!!')

    def drop_all(self):
        self.Base.metadata.drop_all(self.engine)
        print(f'DB drop!!!')

    def get_user(self, user_id):
        user = self.session.get(Users, user_id)
        return user

    def add_user(self, user_id):
        new_user = Users(id=user_id)
        self.session(new_user)
        self.session.commit()

    def set_search_params(self, user_id, search_params):
        user = self.get_user(user_id)
        if user.params:
            user.params.b_year = search_params['b_year']
            user.params.city = search_params['city']
            user.params.status = search_params['status']
            user.params.gender = search_params['gender']
        else:
            new_params = SearchParams(user_id=user_id,
                                      b_year=search_params['b_year'],
                                      city=search_params['city'],
                                      status=search_params['status'],
                                      gender=search_params['gender'])
            self.session.add(new_params)
        self.session.commit()

    def get_search_params(self, user_id):
        user = self.session.get(Users, user_id)
        if not user:
            return None
        db_params = user.params
        if db_params:
            params = {
                'b_year': db_params.b_year,
                'city': db_params.city,
                'gender': db_params.gender,
                'status': db_params.status
            }
            return params
        else:
            return None

    def add_viewed(self, user_id, viewed_id):
        self.session.get(MergingUsers, user_id, viewed_id).is_viewed = True
        self.session.commit()

    def get_searched_id(self, user_id):
        """
        Будет возвращать найденную страницу, которую ищет пользователь, если не будет найденных возвращает None

        """

        searched_list = self.session.query(MergingUsers).filter(
            MergingUsers.user_id_from == user_id,
            MergingUsers.is_viewed == False).all()

        if not searched_list:
            return None

        self.add_viewed(user_id, searched_list[0].user_id_to)
        return searched_list[0].user_id_to

    def add_searched_users(self, user_id, searched_list_id):
        """
        Здесь будем сохронять найденные варианты в базу

        """
        for searched_id in searched_list_id:
            if not self.get_user(searched_id):
                self.add_user(searched_id)

            searched_user = self.session.get(MergingUsers, user_id,
                                             searched_id)

            if searched_user:
                searched_user.is_viewd = False

            else:
                self.session.add(
                    MergingUsers(user_id_from=user_id, user_id_to=searched_id))

        self.session.commit

    def delete_searched(self, user_id):
        del_search = self.get_user(user_id).user_to

        for search_del in del_search:
            self.session.delete(search_del)

        self.session.commit()

    def add_favorite_user(self, user_id, favorite_id):
        self.session.get(MergingUsers, user_id, favorite_id).is_favotite = True
        self.session.commit()

    def delete_favorite(self, user_id, favorite_id):
        self.session.get(MergingUsers, user_id,
                         favorite_id).is_favorite = False
        self.session.commit()

    def get_favorite_user(self, user_id):
        favorite_list = self.session.query(MergingUsers).filter(
            MergingUsers.user_id_from == user_id,
            MergingUsers.is_favorite == True).all()
        return favorite_list
