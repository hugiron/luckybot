import os
import re
import json
import argparse
import datetime
import logging
import multiprocessing as mp
from importlib.machinery import SourceFileLoader
from mongoengine import connect

from luckybot.util.normalizer import Normalizer
from luckybot.model.naive_bayes import NaiveBayesModel
from luckybot.model.contest import Contest
from luckybot.model.group import GroupModel
from luckybot.model.group_meta import GroupMeta
from luckybot.util.logger import init_logger


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--folder', type=str, default='data',
                        help='Name of folder with output dataset')
    parser.add_argument('-p', '--prefix', type=str, default='ds',
                        help='Prefix of file with output dataset')
    parser.add_argument('-m', '--model', type=str, default='objects/bayes.model',
                        help='Path to Naive Bayes model')
    parser.add_argument('-g', '--group', type=str, default='objects/group_city.model',
                        help='Path to model with pairs from group_id and city_id')
    parser.add_argument('--group_meta', type=str, default='objects/group_meta.model',
                        help='Path to model with approved groups and screen names')
    parser.add_argument('-t', '--threshold', type=float, default=0.9,
                        help='Threshold value for the classifier')
    parser.add_argument('-a', '--alpha', type=float, default=1,
                        help='Smoothing factor for the classifier')
    return parser.parse_args()


def validate_vk_url(vk_url):
    name = vk_url.split('/')[-1]
    if name.startswith('id') and name[2:].isdigit():
        return '{vk_user}'
    elif name.startswith('club') and name[4:].isdigit() or group_meta.is_group(name):
        return '{vk_group}'
    return '{vk_url}'


def parse_date(text, publish_date):
    def datetime_from_weekday(weekday):
        try:
            date = publish_date + datetime.timedelta(days=weekday + 7 - publish_date.weekday()
                                                     if weekday <= publish_date.weekday()
                                                     else weekday - publish_date.weekday())
            return date
        except Exception as msg:
            logging.error('%s\n%s' % (str(msg), json.dumps(dict(weekday=weekday))))
            return None

    def datetime_from_full_date(date):
        try:
            day, month, year = map(int, date.split('.'))
            if month < 1 or month > 12 or day < 1 or day > 31:
                return None
            if year < 2000:
                year += 2000
            return datetime.date(day=day, month=month, year=year)
        except Exception as msg:
            logging.error('%s\n%s' % (str(msg), json.dumps(dict(date=str(date)))))
            return None

    def datetime_from_short_date(date):
        try:
            day, month = map(int, date.split('.'))
            if month < 1 or month > 12 or day < 1 or day > 31:
                return None
            year = publish_date.year
            date = datetime.date(day=day, month=month, year=year)
            if publish_date > date:
                date = datetime.date(day=day, month=month, year=year + 1)
            return date
        except Exception as msg:
            logging.error('%s\n%s' % (str(msg), json.dumps(dict(date=str(date)))))
            return None

    for i, month in enumerate(months):
        text = text.replace(month, ".%d." % (i + 1))

    full_date = [date for date in full_date_regex.findall(text.replace(' ', '')) if '.' in date]
    short_date = short_date_regex.findall(text.replace(' ', ''))
    weekday_date = [weekdays[word] for word in text.split() if word in weekdays]

    dates = list(filter(lambda x: x, list(map(datetime_from_full_date, full_date)) +
                        list(map(datetime_from_short_date, short_date)) +
                        list(map(datetime_from_weekday, weekday_date))))
    return min(dates) if dates else None


def classifier(filename):
    try:
        current_date = datetime.date.today()
        with open(filename, 'r') as file_corpus:
            for post in file_corpus:
                try:
                    if not post.strip():
                        continue
                    post_id, publish_date, text = post.strip().split('\t')
                    group_id = int(post_id.split('_')[0][1:])
                    norm_text = normalizer.normalize(text, validate_vk_url)
                    if model.classify(norm_text, args.alpha)[0] >= args.threshold:
                        text = normalizer.text_normalize(text)
                        date = parse_date(text=text, publish_date=datetime.datetime.fromtimestamp(int(publish_date)).date())
                        if date and date > current_date and group_meta.is_approved(group_id) and \
                                        '{vk_group}' in norm_text and '{vk_user}' not in norm_text and '{url}' not in norm_text:
                            contest = Contest.create(post_id, text, date, group[int(post_id.split('_')[0][1:])], [])
                            contest.save()
                except Exception as msg:
                    logging.error(str(msg))
        os.remove(filename)
    except Exception as msg:
        logging.error('%s\n%s' % (str(msg), json.dumps(dict(filename=filename))))


def initializer():
    global model, normalizer, group, database, group_meta
    model = NaiveBayesModel.load(args.model)
    group = GroupModel.load(args.group)
    group_meta = GroupMeta.load(args.group_meta)
    normalizer = Normalizer()
    database = connect(db=config.mongo_database, host=config.mongo_host, port=int(config.mongo_port),
                       username=config.mongo_username, password=config.mongo_password)

    global full_date_regex, short_date_regex, months, weekdays
    months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь',
              'декабрь']
    weekdays = {weekday: i for i, weekday in enumerate(['понедельник', 'вторник', 'среда', 'четверг', 'пятница',
                                                        'суббота', 'воскресение'])}
    full_date_regex = re.compile(r'\d{1,2}\.\d{1,2}\.(\d{4}|\d{2})')
    short_date_regex = re.compile(r'\d{1,2}\.\d{1,2}')


if __name__ == '__main__':
    try:
        init_logger()
        global args, config
        # Парсинг аргументов командной строки
        args = parse_args()
        config = SourceFileLoader('*', 'server.conf').load_module()
        files = list(map(lambda x: "%s/%s" % (args.folder, x),
                         filter(lambda x: x.startswith(args.prefix) and x.endswith('.list'), os.listdir(args.folder))))
        for file in files:
            os.rename(file, "%s.tmp" % file)
        files = ["%s.tmp" % file for file in files]
        if len(files) > 1:
            with mp.Pool(min(mp.cpu_count(), len(files)), initializer=initializer) as pool:
                pool.map(classifier, files)
        elif files:
            initializer()
            classifier(files[0])
    except Exception as msg:
        logging.error(str(msg))
