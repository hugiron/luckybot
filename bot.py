import time

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.escape

import asyncmc
from motor.motor_tornado import MotorClient

from luckybot.actor.pool import PoolActor
from luckybot.actor.actor_handler import ActorHandler

from luckybot.model.city import CityModel
from luckybot.model.category import CategoryModel
from luckybot.model.group import GroupModel
from luckybot.model.response_template import ResponseTemplate
from luckybot.util.logger import init_logger

tornado.options.define('port')
tornado.options.define('timeout')

tornado.options.define('access_token')
tornado.options.define('secret_key')
tornado.options.define('group_id')
tornado.options.define('confirmation_code')
tornado.options.define('max_contest_count')
tornado.options.define('max_contest_days')

tornado.options.define('city')
tornado.options.define('category')
tornado.options.define('group')
tornado.options.define('response_template')

tornado.options.define('mongo_host')
tornado.options.define('mongo_port')
tornado.options.define('mongo_database')
tornado.options.define('mongo_username')
tornado.options.define('mongo_password')

tornado.options.define('memcached_server')


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MessageHandler)
        ]

        mongo_url = "mongodb://%s:%s@%s:%s/%s" % (tornado.options.options.mongo_username,
                                                  tornado.options.options.mongo_password,
                                                  tornado.options.options.mongo_host,
                                                  tornado.options.options.mongo_port,
                                                  tornado.options.options.mongo_database)
        self.motor_client = MotorClient(mongo_url)
        self.mc = asyncmc.Client(servers=tornado.options.options.memcached_server.split(','))

        settings = dict(
            autoreload=True,
            debug=True,
            group_id=int(tornado.options.options.group_id),
            confirmation_code=tornado.options.options.confirmation_code,
            timeout=int(tornado.options.options.timeout)
        )
        pool_settings = dict(
            access_token=tornado.options.options.access_token,
            city=CityModel.load(tornado.options.options.city),
            category=CategoryModel.load(tornado.options.options.category),
            group=GroupModel.load(tornado.options.options.group),
            response_template=ResponseTemplate.load(tornado.options.options.response_template),
            group_id=tornado.options.options.group_id,
            max_contest_count=int(tornado.options.options.max_contest_count),
            max_contest_days=int(tornado.options.options.max_contest_days),
            db=self.motor_client[tornado.options.options.mongo_database],
            mc=self.mc
        )

        tornado.web.Application.__init__(self, handlers, **settings)
        self.actor_pool = PoolActor(ActorHandler, **pool_settings)


class MessageHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if data['type'] == 'confirmation' and data['group_id'] == self.settings['group_id']:
            self.write(self.settings['confirmation_code'])
        else:
            self.write('ok')

            user_id = data['object']['user_id']
            current_time = int(time.time())
            key = 'time_%d' % user_id
            last_appeal = yield self.application.mc.get(key)
            if last_appeal and current_time - last_appeal <= self.settings['timeout']:
                return
            yield self.application.mc.set(key, current_time)

            if data.get('secret') == tornado.options.options.secret_key:
                self.application.actor_pool.proxy().parse(data)


def main():
    tornado.options.parse_config_file('server.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)

    print("Start listening...")
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    init_logger()
    main()
