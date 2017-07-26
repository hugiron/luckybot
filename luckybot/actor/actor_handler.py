import pykka
from mongoengine import connect


class ActorHandler(pykka.ThreadingActor):
    def __init__(self, pool, group, city, category, access_token, mongo_host, mongo_port, mongo_username,
                 mongo_password, mongo_database):
        super(ActorHandler, self).__init__()
        self.pool = pool
        self.group = group
        self.city = city
        self.category = category
        self.access_token = access_token
        self.db = connect(db=mongo_database, host=mongo_host, port=mongo_port, username=mongo_username,
                          password=mongo_password)

    """
        Scheme:
        {
            type: <str>,
            object: <object>,
            group_id: <int>
        }
    """
    def parse(self, message):
        pass

    """
        Scheme:
        {
            command: <str>,
            user_id: <int>,
            data: <object>
        }
    """
    def handle(self, message):
        pass

    """
        Scheme:
        {
            type: <str>,
            user_id: <int>,
            data: <object>
        }
    """
    def send(self, message):
        pass
