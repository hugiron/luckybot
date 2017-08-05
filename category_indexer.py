import argparse
from importlib.machinery import SourceFileLoader
from mongoengine import connect

from luckybot.model.category import CategoryModel
from luckybot.model.contest import Contest
from luckybot.util.logger import init_logger


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--category', type=str, default='objects/category.json',
                        help='The number of days through which the last contests are deleted')
    return parser.parse_args()


if __name__ == '__main__':
    init_logger()
    args = parse_args()
    config = SourceFileLoader('*', 'server.conf').load_module()
    database = connect(db=config.mongo_database, host=config.mongo_host, port=int(config.mongo_port),
                       username=config.mongo_username, password=config.mongo_password)
    category = CategoryModel.load(args.category)
    posts = set()
    for category_id, keywords in category.keywords.items():
        if keywords:
            query = ' '.join(keywords)
            for contest in Contest.objects(is_tagged=False).search_text(query, language='ru'):
                posts.add(contest.post_id)
                contest.update(push__category=category_id)
    if posts:
        Contest.objects(post_id__in=list(posts)).update(set__is_tagged=True)
