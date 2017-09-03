import os

import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

import memcache

from luckybot.util.logger import init_logger

tornado.options.define('landing_port')
tornado.options.define('memcached_server')


class Application(tornado.web.Application):
    def __init__(self):
        #self.memcached = memcache.Client(servers=tornado.options.options.memcached_server.split(','))
        handlers = [
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static/landing'}),
            (r'/', LandingHandler)
        ]
        tornado.web.Application.__init__(self, handlers, autoreload=True, debug=True)


class LandingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        return self.render('view/landing/index.html')


def main():
    tornado.options.parse_config_file('server.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.landing_port)

    print("Start listening...")
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    init_logger()
    main()
