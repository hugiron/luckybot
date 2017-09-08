import argparse
import logging
import time

import vk

from luckybot.util.logger import init_logger
from luckybot.util.normalizer import Normalizer
from luckybot.util.transliterator import translit
from luckybot.model.access_token import AccessToken
from luckybot.model.group_meta import GroupMeta
from luckybot.model.city import CityModel
from luckybot.model.group import GroupModel


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tokens', type=str, default='objects/access_token.json',
                        help='Path to file with access tokens for VK API')
    parser.add_argument('-b', '--begin', type=int, default=1,
                        help='Begin group ID for indexer')
    parser.add_argument('-e', '--end', type=int, default=150000000,
                        help='End group ID for indexer')
    parser.add_argument('--count', type=int, default=500,
                        help='Groups count of one request')
    parser.add_argument('-c', '--city', type=str, default='objects/city.json',
                        help='Path to file with binary dump cities')
    parser.add_argument('-m', '--members', type=int, default=500,
                        help='Min count of members in group')
    parser.add_argument('--group_city', type=str, default='objects/group_city.model',
                        help='Path to model with pairs from group_id and city_id')
    parser.add_argument('--group_meta', type=str, default='objects/group_meta.model',
                        help='Path to model with approved groups and screen names')
    return parser.parse_args()


if __name__ == '__main__':
    init_logger()
    # Парсинг аргументов командной строки
    args = parse_args()
    begin_id = args.begin
    group_city = GroupModel()
    group_meta = GroupMeta()

    # Список сервисных токенов доступа к VK API
    access_token = AccessToken(args.tokens)
    cities = CityModel.load(args.city)
    # Нормализатор текста (переводит исходный текст в нормальную форму)
    normalizer = Normalizer()

    # Настройка подключения к VK API
    session = vk.Session()
    api = vk.API(session, v='5.65', lang='ru')

    # Количество запросов, которые требуется отправить к VK API
    count = (args.end - begin_id) // args.count + 1
    for page in range(count):
        while True:
            try:
                # Начальный и конечный идентификаторы сообществ для запроса
                end_id = min(args.end + 1, begin_id + args.count)
                if not begin_id < end_id:
                    break
                data = api.groups.getById(group_ids=','.join(map(str, range(begin_id, end_id))),
                                          fields='members_count,city', access_token=access_token())

                for current in data:
                    begin_id = current['id'] + 1
                    if 'members_count' not in current or current['members_count'] < args.members:
                        continue
                    # Сохранение данных в модель с мета-информацией
                    group_meta.add(current['id'], current.get('screen_name'))

                    # Сохранение данных в модель с информацией о геолокации сообществ
                    text = '%s' % (current.get('name'))
                    text = (' '.join(normalizer.mystem.lemmatize(text))).replace('-', ' ').replace('–', ' ').split()
                    group_city[current['id']] = cities[map(translit, filter(lambda x: x.isalpha(), text))]
                    if 'city' in current and current['city']['id'] not in group_city[current['id']]:
                        group_city[current['id']].append(current['city']['id'])
                break
            except Exception as msg:
                logging.error(str(msg))
                time.sleep(1)

    group_city.save(args.group_city)
    group_meta.save(args.group_meta)
