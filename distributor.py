import vk
import argparse
import datetime
import random
import logging
from functools import reduce
from importlib.machinery import SourceFileLoader
from mongoengine import connect

from luckybot.model.contest import Contest
from luckybot.model.user import User
from luckybot.model.response_template import ResponseTemplate
from luckybot.model.access_token import AccessToken
from luckybot.util.logger import init_logger
from luckybot.util.normalizer import Normalizer


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--size_cut', type=int, default=24,
                        help='The number of the best contests, from which random ones will be selected to be sent to the user')
    parser.add_argument('-c', '--count', type=int, default=8,
                        help='Maximum number of contests to be sent to each user')
    parser.add_argument('-t', '--tokens', type=str, default='objects/access_token.json',
                        help='Path to file with access tokens for VK API')
    return parser.parse_args()


def build_dict_by_city(contests):
    result = dict()
    for contest in contests:
        if contest.city:
            result[contest.post_id] = set(contest.city)
    return result


def build_dict_by_category(contests):
    result = dict()
    for contest in contests:
        for category in contest.category:
            if category not in result:
                result[category] = set()
            result[category].add(contest.post_id)
    return result


def build_dict_by_word(contests):
    result = dict()
    for contest in contests:
        for word in contest.text.split():
            if word not in result:
                result[word] = set()
            result[word].add(contest.post_id)
    return result


def calculate_factor(contests, access_token):
    def batching(array, batch_size=100):
        for i in range((len(array) - 1) // batch_size + 1):
            yield array[i * batch_size:(i + 1) * batch_size]

    vk_session = vk.Session()
    vk_api = vk.API(vk_session, v='5.65', lang='ru')
    result = dict()
    groups = dict()
    for batch in batching(list(map(lambda x: x.post_id.split('_')[0][1:], contests))):
        for group in vk_api.groups.getById(group_ids=','.join(batch), access_token=access_token(), fields='members_count'):
            if 'members_count' in group:
                groups[-group['id']] = group['members_count']
    for batch in batching(list(map(lambda x: x.post_id, contests))):
        for post in vk_api.wall.getById(posts=','.join(batch), access_token=access_token()):
            post_id = '%d_%d' % (post['owner_id'], post['id'])
            if post['owner_id'] in groups and groups[post['owner_id']]:
                if 'views' in post:
                    result[post_id] = post['views']['count'] / groups[post['owner_id']]
                else:
                    result[post_id] = post['reposts']['count'] / groups[post['owner_id']]
            else:
                result[post_id] = 0
    return result


def search_target_contest(user, contest_city, contest_category, contest_word):
    def post_in_user_city(post_id):
        return post_id not in contest_city or contest_city[post_id].intersection(user.city)

    result = set()
    if user.category:
        for category in user.category:
            if category in contest_category:
                for post_id in contest_category[category]:
                    if post_in_user_city(post_id):
                        result.add(post_id)
    else:
        result = set([post_id for category, posts in contest_category.items()
                      for post_id in posts if post_in_user_city(post_id)])
    for gift in user.gift:
        keywords = normalizer.text_normalize(gift).split()
        is_full = True
        for word in keywords:
            is_full &= word in contest_word
        if is_full:
            bag_words = list(map(lambda word: contest_word[word], keywords))
            if bag_words:
                for post_id in reduce(lambda x, y: x.intersection(y), bag_words):
                    if post_in_user_city(post_id):
                        result.add(post_id)
    return result


if __name__ == '__main__':
    try:
        global args
        init_logger()
        args = parse_args()
        config = SourceFileLoader('*', 'server.conf').load_module()
        database = connect(db=config.mongo_database, host=config.mongo_host, port=int(config.mongo_port),
                           username=config.mongo_username, password=config.mongo_password)
        template = ResponseTemplate.load(config.response_template)
        access_token = AccessToken(args.tokens)

        global normalizer
        normalizer = Normalizer()

        vk_session = vk.Session(access_token=config.access_token)
        vk_api = vk.API(vk_session, v='5.65', lang='ru')

        current_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()) + datetime.timedelta(days=1)
        contests = list(Contest.objects(date=current_date))
        contest_city = build_dict_by_city(contests)
        contest_category = build_dict_by_category(contests)
        contest_word = build_dict_by_word(contests)
        contest_factor = calculate_factor(contests, access_token)
    except Exception as msg:
        logging.error(str(msg))

    for user in User.objects():
        try:
            user_contest = list(map(lambda item: (item, contest_factor[item] if item in contest_factor else 0),
                                    search_target_contest(user, contest_city, contest_category, contest_word)))
            user_contest.sort(key=lambda item: -item[1])
            user_contest = random.sample(user_contest[:args.size_cut], min(args.count, len(user_contest)))
            user_contest.sort(key=lambda item: -item[1])
            user_contest = list(map(lambda x: x[0], user_contest))
            if user_contest:
                message = template.render('distribute_contest',
                                          list(map(lambda item: 'https://vk.com/wall%s' % item, user_contest[1:])))[0]
                if not user.is_member:
                    message += '<br><br>' + template.get_text('agitation')
                vk_api.messages.send(user_id=user.user_id, message=message, attachment='wall%s' % user_contest[0])
        except Exception as msg:
            logging.error(str(msg))
