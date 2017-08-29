import vk
import operator
import argparse
import datetime
import logging
from importlib.machinery import SourceFileLoader
from mongoengine import connect

from luckybot.util.logger import init_logger
from luckybot.model.access_token import AccessToken
from luckybot.model.contest import Contest

from distributor import calculate_factor


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tokens', type=str, default='objects/access_token.json',
                        help='Path to file with access tokens for VK API')
    parser.add_argument('-n', '--number', type=int, default=100,
                        help='The number of contests that are sent out daily to moderators')
    return parser.parse_args()


if __name__ == '__main__':
    try:
        init_logger()
        args = parse_args()
        config = SourceFileLoader('*', 'server.conf').load_module()
        database = connect(db=config.mongo_database, host=config.mongo_host, port=int(config.mongo_port),
                           username=config.mongo_username, password=config.mongo_password)
        access_token = AccessToken(args.tokens)
        vk_session = vk.Session(access_token=config.access_token)
        vk_api = vk.API(vk_session, v='5.65', lang='ru')

        date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()) + datetime.timedelta(days=1)
        contests = list(Contest.objects(date=date, city__size=0))
        contest_factor = calculate_factor(contests, access_token)
        contests = sorted(contest_factor.items(), key=operator.itemgetter(1))
        contests.reverse()
        posts = [post_id for post_id, factor in contests[:args.number]]
        message = '<br>'.join(['[%d] https://vk.com/wall%s' % (index + 1, post_id) for index, post_id in enumerate(posts)])

        receivers = vk_api.groups.getMembers(group_id=config.group_id, filter='managers')['items']
        user_ids = ','.join(map(lambda member: str(member['id']), receivers))
        vk_api.messages.send(user_ids=user_ids, message=message)
    except Exception as msg:
        logging.error(str(msg))
