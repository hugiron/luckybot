from mongoengine.document import Document
from mongoengine.fields import StringField, IntField, ListField, DateTimeField


class Contest(Document):
    post_id = StringField(required=True)
    text = StringField(required=True)
    date = DateTimeField(required=True)
    city = ListField(IntField())
    category = ListField(StringField())

    meta = {
        'collection': 'contest',
        'indexes': [
            '#post_id',
            'date',
            'city',
            'category',
            {
                'fields': ['$text'],
                'default_language': 'russian'
            }
        ]
    }

    def __init__(self, post_id, text, date, city, category):
        super(Contest, self).__init__()
        self.post_id = post_id
        self.text = text
        self.date = date
        self.city = city
        self.category = category
