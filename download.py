import vk
import os
import time
import argparse
import logging
from importlib.machinery import SourceFileLoader
from mongoengine import connect

from luckybot.util.logger import init_logger
from luckybot.util.normalizer import Normalizer
from luckybot.model.contest import Contest
from luckybot.model.access_token import AccessToken


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delete', default=False, action='store_true',
                        help='Do I need to delete the post after saving to a file?')
    parser.add_argument('-t', '--tokens', type=str, default='objects/access_token.json',
                        help='Path to file with access tokens for VK API')
    parser.add_argument('-p', '--prefix', type=str, default='data/ds',
                        help='Prefix of file with output dataset')
    return parser.parse_args()


if __name__ == '__main__':
    try:
        init_logger()
        args = parse_args()
        normalizer = Normalizer()
        config = SourceFileLoader('*', 'server.conf').load_module()
        database = connect(db=config.mongo_database, host=config.mongo_host, port=int(config.mongo_port),
                           username=config.mongo_username, password=config.mongo_password)
        access_token = AccessToken(args.tokens)
        vk_session = vk.Session()
        vk_api = vk.API(vk_session, v='5.65', lang='ru')

        def batching(array, batch_size=100):
            for i in range((len(array) - 1) // batch_size + 1):
                yield array[i * batch_size:(i + 1) * batch_size]

        posts = [contest.post_id for contest in Contest.objects()]
        filename = "%s_%s.list" % (args.prefix, time.strftime("%Y_%m_%d_%H:%M", time.gmtime()))
        with open("%s.tmp" % filename, 'w') as dataset:
            for batch in batching(posts):
                for post in vk_api.wall.getById(posts=','.join(batch), access_token=access_token()):
                    post_id = '%d_%d' % (post['owner_id'], post['id'])
                    dataset.write("%s\t%d\t%s\n" % (post_id, post['date'], normalizer.preprocess(post['text'])))

        if args.delete:
            Contest.objects(post_id__in=posts).delete()
        os.rename("%s.tmp" % filename, filename)
    except Exception as msg:
        logging.error(str(msg))
