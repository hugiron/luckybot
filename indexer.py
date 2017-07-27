import argparse
import time

import vk

from luckybot.util.normalizer import Normalizer
from luckybot.util.transliterator import translit
from luckybot.model.city import CityModel
from luckybot.model.group import GroupModel
from luckybot.model.access_token import AccessToken


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tokens', type=str, default='objects/access_token.json',
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
    parser.add_argument('-o', '--output', type=str, default='objects/group.model',
                        help='Path to file with groups location')
    return parser.parse_args()


if __name__ == '__main__':
    # Парсинг аргументов командной строки
    args = parse_args()
    begin_id = args.begin
    group = GroupModel()

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
                data = api.groups.getById(group_ids=','.join(map(str, range(begin_id, end_id))), fields='members_count',
                                          access_token=access_token())
                # Сохранение только тех сообществ, которые относятся к определенному городу
                for current in data:
                    begin_id = current['id'] + 1
                    if 'members_count' not in current or current['members_count'] < args.members:
                        continue
                    group[current['id']] = cities[map(translit, normalizer.normalize(current['name']))]
                break
            except Exception as msg:
                print(msg)
                time.sleep(1)
    group.save(args.output)
