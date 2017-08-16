import argparse
import os
import time
import json
import logging

import vk

from luckybot.util.normalizer import Normalizer
from luckybot.model.access_token import AccessToken
from luckybot.util.logger import init_logger


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keywords', type=str, default='objects/keyword.json',
                        help='Path to file with keywords for search')
    parser.add_argument('-t', '--tokens', type=str, default='objects/access_token.json',
                        help='Path to file with access tokens for VK API')
    parser.add_argument('-p', '--prefix', type=str, default='data/ds',
                        help='Prefix of file with output dataset')
    parser.add_argument('-c', '--count', type=int, default=200,
                        help='Max count of posts in result for one keyword')
    parser.add_argument('--history', type=str, default='data/history.list',
                        help='Path to file with handled post ids')
    parser.add_argument('-d', '--delay', type=int, default=2880,
                        help='How many minutes posts are stored in the history')
    return parser.parse_args()


if __name__ == '__main__':
    try:
        init_logger()
        # Парсинг аргументов командной строки
        args = parse_args()
        # Генерация суффикса файла из текущей даты и времени
        filename = "%s_%s.list" % (args.prefix, time.strftime("%Y_%m_%d_%H:%M", time.gmtime()))
        # Список сервисных токенов доступа к VK API
        access_token = AccessToken(args.tokens)
        # Множество идентификаторов записей, собранных на предыдущих итерациях
        history = {post.strip().split('\t')[0]: int(post.strip().split('\t')[1])
                       for post in open(args.history, 'r') if post.strip()} if os.path.exists(args.history) else dict()
        # Удаление из истории старых записей
        for post_id in list(history):
            if abs(history[post_id] - int(time.time())) >= 60 * args.delay:
                del history[post_id]
        # Список ключевых слов для поиска записей
        with open(args.keywords, 'r') as file:
            keywords = json.load(file)
        # Настройка подключения к VK API
        session = vk.Session()
        api = vk.API(session, v='5.65', lang='ru')
        # Нормализатор текста (переводит исходный текст в нормальную форму)
        normalizer = Normalizer()

        with open("%s.tmp" % filename, 'w') as dataset:
            for keyword in keywords:
                # Поиск записей в новостной ленте ВКонтакте по ключевому запросу
                data = api.newsfeed.search(q=keyword, count=args.count, access_token=access_token())
                for post in data['items']:
                    post_id = "%s_%s" % (post['owner_id'], post['id'])
                    # Если запись была оставлена от имени сообщества, не является репостом и не была ранее обработана
                    if post_id not in history:
                        if post['owner_id'] < 0 and post['post_type'] == 'post':
                            dataset.write("%s\t%d\t%s\n" % (post_id, post['date'], normalizer.preprocess(post['text'])))
                        history[post_id] = int(time.time())

        # Перезапись файла с историей идентификаторов записей
        with open(args.history, 'w') as file:
            for post_id in history:
                file.write("%s\t%d\n" % (post_id, history[post_id]))

        # Переименование файла для дальнейшей обработки распределителем
        os.rename("%s.tmp" % filename, filename)
    except Exception as msg:
        logging.error(str(msg))
