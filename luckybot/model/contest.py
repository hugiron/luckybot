from mongoengine.document import Document
from mongoengine.fields import StringField, IntField, ListField, DateTimeField


class Contest(Document):
    post_id = StringField(required=True)
    text = StringField(required=True)
    date = DateTimeField(required=True)
    city = ListField(IntField())

    meta = {
        'collection': 'contest',
        'indexes': [
            '#post_id',
            'date',
            'city',
            {
                'fields': ['$text'],
                'default_language': 'russian'
            }
        ]
    }

    def __init__(self, post_id, text, date, city):
        super(Contest, self).__init__()
        self.post_id = post_id
        self.text = text
        self.date = date
        self.city = city
