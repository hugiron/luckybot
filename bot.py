import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.escape

from luckybot.actor.pool import PoolActor
from luckybot.actor.actor_handler import ActorHandler

from luckybot.model.city import CityModel
from luckybot.model.category import CategoryModel
from luckybot.model.group import GroupModel

tornado.options.define('port')

tornado.options.define('access_token')
tornado.options.define('secret_key')
tornado.options.define('group_id')
tornado.options.define('confirmation_code')

tornado.options.define('city')
tornado.options.define('category')
tornado.options.define('group')

tornado.options.define('mongo_host')
tornado.options.define('mongo_port')
tornado.options.define('mongo_database')
tornado.options.define('mongo_username')
tornado.options.define('mongo_password')


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MessageHandler)
        ]
        settings = dict(
            autoreload=True,
            debug=True,
            group_id=int(tornado.options.options.group_id),
            confirmation_code=tornado.options.options.confirmation_code
        )
        pool_settings = dict(
            access_token=tornado.options.options.access_token,
            city=CityModel.load(tornado.options.options.city),
            category=CategoryModel.load(tornado.options.options.category),
            group=GroupModel.load(tornado.options.options.group),
            mongo_host=tornado.options.options.mongo_host,
            mongo_port=int(tornado.options.options.mongo_port),
            mongo_username=tornado.options.options.mongo_username,
            mongo_password=tornado.options.options.mongo_password,
            mongo_database=tornado.options.options.mongo_database
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
            if data.get('secret') == tornado.options.options.secret_key:
                self.application.actor_pool.proxy().parse(data)
            self.write('ok')


def main():
    tornado.options.parse_config_file('server.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)

    print("Start listening...")
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
