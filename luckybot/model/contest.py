from mongoengine.document import Document
from mongoengine.fields import StringField, IntField, ListField, DateTimeField, BooleanField


class Contest(Document):
    post_id = StringField(required=True, unique=True)
    text = StringField(required=True)
    date = DateTimeField(required=True)
    city = ListField(IntField())
    category = ListField(StringField())
    is_tagged = BooleanField(required=True, default=False)

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
            },
            'is_tagged'
        ]
    }

    @staticmethod
    def create(post_id, text, date, city, category, is_tagged=False):
        contest = Contest()
        contest.post_id = post_id
        contest.text = text
        contest.date = date
        contest.city = city
        contest.category = category
        contest.is_tagged = is_tagged
        return contest
