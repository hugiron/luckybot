from mongoengine.document import Document
from mongoengine.fields import ListField, IntField, BooleanField, StringField


class User(Document):
    user_id = IntField(required=True)
    is_member = BooleanField(required=True)
    city = ListField(IntField())
    category = ListField(StringField())
    gift = ListField(StringField())

    meta = {
        'collection': 'user',
        'indexes': [
            'user_id',
            'city',
            'category',
            'gift'
        ]
    }

    @staticmethod
    def create(user_id, city, category, gift, is_member):
        user = User()
        user.user_id = user_id
        user.city = city
        user.category = category
        user.gift = gift
        user.is_member = is_member
        return user
