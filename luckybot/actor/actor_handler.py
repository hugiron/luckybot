import logging
import tornado.ioloop
import tornado.gen
import pykka
import vk
import json

from luckybot.util.message_parser import MessageParser
from luckybot.util.handler import Handler


class ActorHandler(pykka.ThreadingActor):
    def __init__(self, pool, group, city, category, access_token, response_template, group_id, max_contest_count,
                 max_contest_days, db, mc):
        super(ActorHandler, self).__init__()
        self.pool = pool
        self.group = group
        self.city = city
        self.category = category
        self.access_token = access_token
        self.response_template = response_template
        self.group_id = group_id
        self.max_contest_count = max_contest_count
        self.max_contest_days = max_contest_days
        self.db = db
        self.mc = mc

        self.message_parser = MessageParser(self.city, self.category)
        self.handler = Handler(self.db, self.mc, self.city, self.category, self.group_id, self.max_contest_count,
                               self.max_contest_days)

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
    @tornado.gen.coroutine
    def parse(self, message):
        try:
            if message['type'] == 'message_new':
                self.pool.proxy().handle(self.message_parser.parse(message['object']['body'],
                                                                   message['object']['user_id']))
            else:
                self.pool.proxy().handle(dict(command=message['type'], user_id=message['object']['user_id'], data=None))
        except Exception as exc:
            logging.error('%s\n%s' % (str(exc), json.dumps(message)))

    """
        Scheme:
        {
            command: <str>,
            user_id: <int>,
            data: <object>
        }
    """
    @tornado.gen.coroutine
    def handle(self, message):
        try:
            if 'command' in message and message['command'] in self.handler.handlers:
                msg = yield self.handler.handlers[message['command']](message['user_id'], message.get('data'))
            else:
                msg = dict(
                    type='not_recognized',
                    user_id=message['user_id']
                )
            self.pool.proxy().send(msg)
        except Exception as exc:
            logging.error('%s\n%s' % (str(exc), json.dumps(message)))

    """
        Scheme:
        {
            type: <str>,
            user_id: <int>,
            data: <object>,
            attach: <list<str>>
        }
    """
    @tornado.gen.coroutine
    def send(self, message):
        try:
            response = self.response_template.render(message['type'], message.get('data'))
            if message:
                try:
                    if response[0] or message.get('attach'):
                        self.vk_api.messages.send(user_id=message['user_id'], message=response[0],
                                                  attachment=','.join(message['attach']) if 'attach' in message else '')
                    if response[1]:
                        self.vk_api.messages.send(user_id=message['user_id'], sticker_id=response[1])
                except Exception as msg:
                    if msg.__dict__['error_data']['error_code'] != 901:
                        logging.error(str(msg))
                        self.pool.proxy().send(message)
        except Exception as exc:
            logging.error('%s\n%s' % (str(exc), json.dumps(message)))
