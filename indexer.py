import argparse
import pickle
import random

import vk

from luckybot.util.normalizer import Normalizer
from luckybot.util.transliterator import translit
from luckybot.model.city import CityModel


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tokens', type=str, default='resources/access_token.list',
                        help='Path to file with access tokens for VK API')
    parser.add_argument('-b', '--begin', type=int, default=1,
                        help='Begin group ID for indexer')
    parser.add_argument('-e', '--end', type=int, default=149585000,
                        help='End group ID for indexer')
    parser.add_argument('--count', type=int, default=500,
                        help='Groups count of one request')
    parser.add_argument('-c', '--city', type=str, default='objects/city.model',
                        help='Path to file with binary dump cities')
    parser.add_argument('-m', '--members', type=int, default=1000,
                        help='Min count of members in group')
    parser.add_argument('-o', '--output', type=str, default='resources/group.pickle',
                        help='Path to file with groups location')
    return parser.parse_args()


if __name__ == '__main__':
    # Парсинг аргументов командной строки
    args = parse_args()
    begin_id = args.begin
    groups = dict()

    # Список сервисных токенов доступа к VK API
    access_token = [token.strip() for token in open(args.tokens, 'r') if token.strip()]
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
                start_id = begin_id + page * args.count
                end_id = min(args.end + 1, start_id + args.count)
                data = api.groups.getById(group_ids=','.join(map(str, range(start_id, end_id))), fields='members_count',
                                          access_token=random.choice(access_token))
                # Сохранение только тех сообществ, которые относятся к определенному городу
                for group in data:
                    begin_id = group['id']
                    if 'members_count' not in group or group['members_count'] < args.members:
                        continue
                    current = cities[map(translit, normalizer.normalize(group['name']))]
                    if current:
                        groups[group['id']] = current
                break
            except:
                pass

    with open(args.output, 'wb') as file:
        pickle.dump(groups, file)
