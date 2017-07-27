import pykka
from mongoengine import connect
import vk

from luckybot.util.message_parser import MessageParser


class ActorHandler(pykka.ThreadingActor):
    def __init__(self, pool, group, city, category, access_token, response_template,
                 mongo_host, mongo_port, mongo_username, mongo_password, mongo_database):
        super(ActorHandler, self).__init__()
        self.pool = pool
        self.group = group
        self.city = city
        self.category = category
        self.access_token = access_token
        self.response_template = response_template
        self.message_parser = MessageParser(self.city, self.category)

        self.db = connect(db=mongo_database, host=mongo_host, port=mongo_port, username=mongo_username,
                          password=mongo_password)

        self.vk_session = vk.Session(access_token=access_token)
        self.vk_api = vk.API(self.vk_session, v='5.65', lang='ru')

    """
        Scheme:
        {
            type: <str>,
            object: <object>,
            group_id: <int>
        }
    """
    def parse(self, message):
        if message['type'] == 'message_new':
            self.pool.proxy().handle(self.message_parser.parse(message['object']['body'], message['object']['user_id']))
        else:
            self.pool.proxy().handle(dict(command=message['type'], user_id=message['object']['user_id']))

    """
        Scheme:
        {
            command: <str>,
            user_id: <int>,
            data: <object>
        }
    """
    def handle(self, message):
        print(message)
        self.pool.proxy().send(dict(
            type='success',
            data=[1,2,3,4,5],
            attach=['wall-77270571_268223'],
            user_id=message['user_id']
        ))

    """
        Scheme:
        {
            type: <str>,
            user_id: <int>,
            data: <object>,
            attach: <list<str>>
        }
    """
    def send(self, message):
        response = self.response_template.render(message['type'], message.get('data'))
        if message:
            try:
                if response[0] or message.get('attach'):
                    self.vk_api.messages.send(user_id=message['user_id'], message=response[0],
                                              attachment=','.join(message['attach']) if 'attach' in message else '')
                if response[1]:
                    self.vk_api.messages.send(user_id=message['user_id'], sticker_id=response[1])
            except Exception as msg:
                print(msg)
                self.pool.proxy().send(message)
