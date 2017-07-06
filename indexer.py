import random
import argparse
import pickle

import vk

from util.normalizer import Normalizer
from util.transliterator import translit


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tokens', type=str, default='metadata/access_token.list',
                        help='Path to file with access tokens for VK API')
    parser.add_argument('-b', '--begin', type=int, default=1,
                        help='Begin group ID for indexer')
    parser.add_argument('-e', '--end', type=int, default=149585000,
                        help='End group ID for indexer')
    parser.add_argument('-c', '--count', type=int, default=500,
                        help='Groups count of one request')
    parser.add_argument('-l', '--list', type=str, default='metadata/city.pickle',
                        help='Path to file with binary dump cities')
    parser.add_argument('-m', '--members', type=int, default=1000,
                        help='Min count of members in group')
    parser.add_argument('-o', '--output', type=str, default='metadata/group.pickle',
                        help='Path to file with groups location')
    return parser.parse_args()


if __name__ == '__main__':
    # Парсинг аргументов командной строки
    args = parse_args()
    begin_id = args.begin
    groups = dict()

    # Список сервисных токенов доступа к VK API
    access_token = [token.strip() for token in open(args.tokens, 'r') if token.strip()]
    with open(args.list, 'rb') as file:
        cities = pickle.load(file)

    while True:
        try:
            # Настройка подключения к VK API
            session = vk.Session()
            api = vk.API(session, v='5.65', lang='ru')
            # Нормализатор текста (переводит исходный текст в нормальную форму)
            normalizer = Normalizer()

            # Количество запросов, которые требуется отправить к VK API
            count = (args.end - begin_id) // args.count + 1
            for page in range(count):
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
                    current = {cities[lex] for lex in map(translit, normalizer.normalize(group['name'])) if lex in cities}
                    if current:
                        groups[group['id']] = list(current)
            break
        except:
            pass

    with open(args.output, 'wb') as file:
        pickle.dump(groups, file)
