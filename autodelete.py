import argparse
import datetime
from importlib.machinery import SourceFileLoader
from mongoengine import connect, Q

from luckybot.model.contest import Contest
from luckybot.util.logger import init_logger


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--delay', type=int, default=1,
                        help='The number of days through which the last contests are deleted')
    return parser.parse_args()


if __name__ == '__main__':
    init_logger()
    args = parse_args()
    config = SourceFileLoader('*', 'server.conf').load_module()
    database = connect(db=config.mongo_database, host=config.mongo_host, port=int(config.mongo_port),
                       username=config.mongo_username, password=config.mongo_password)
    current_date = datetime.datetime.now()
    current_date -= datetime.timedelta(days=args.delay, hours=current_date.hour, minutes=current_date.minute,
                                       seconds=current_date.second, microseconds=current_date.microsecond)
    Contest.objects(Q(date__lt=current_date)).delete()
