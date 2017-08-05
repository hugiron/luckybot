import __main__
import os
import logging


def init_logger(dir='log'):
    if not os.path.exists(dir):
        os.mkdir(dir)
    logging.basicConfig(level=logging.ERROR, filename='%s/%s.log' % (dir, __main__.__file__[:-3]),
                        format=u'%(filename)s[LINE:%(lineno)d] #%(levelname)s [%(asctime)s] %(message)s')
