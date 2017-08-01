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

    def __init__(self, user_id, city, category, gift, is_member):
        super(User, self).__init__()
        self.user_id = user_id
        self.city = city
        self.category = category
        self.gift = gift
        self.is_member = is_member
