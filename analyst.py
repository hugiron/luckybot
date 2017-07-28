import os
import re
import argparse
import datetime
import multiprocessing as mp
from importlib.machinery import SourceFileLoader
from mongoengine import connect

from luckybot.util.normalizer import Normalizer
from luckybot.model.naive_bayes import NaiveBayesModel
from luckybot.model.contest import Contest
from luckybot.model.group import GroupModel


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--folder', type=str, default='data',
                        help='Name of folder with output dataset')
    parser.add_argument('-p', '--prefix', type=str, default='ds',
                        help='Prefix of file with output dataset')
    parser.add_argument('-m', '--model', type=str, default='objects/bayes.model',
                        help='Path to Naive Bayes model')
    parser.add_argument('-g', '--group', type=str, default='objects/group.model',
                        help='Path to model with pairs from group_id and city_id')
    parser.add_argument('-t', '--threshold', type=float, default=0.99,
                        help='Threshold value for the classifier')
    parser.add_argument('-a', '--alpha', type=float, default=1,
                        help='Smoothing factor for the classifier')
    return parser.parse_args()


def parse_date(post, publish_date):
    def datetime_from_weekday(weekday):
        try:
            date = publish_date + datetime.timedelta(days=weekday + 7 - publish_date.weekday()
                                                     if weekday <= publish_date.weekday()
                                                     else weekday - publish_date.weekday())
            return date - datetime.timedelta(hours=publish_date.hour, minutes=publish_date.minute,
                                             seconds=publish_date.second, microseconds=publish_date.microsecond)
        except:
            return None

    def datetime_from_full_date(date):
        try:
            day, month, year = map(int, date.split('.'))
            if year < 2000:
                year += 2000
            return datetime.date(day=day, month=month, year=year)
        except:
            return None

    def datetime_from_short_date(date):
        try:
            day, month = map(int, date.split('.'))
            year = publish_date.year
            date = datetime.date(day=day, month=month, year=year)
            if publish_date > date:
                date = datetime.date(day=day, month=month, year=year + 1)
            return date
        except:
            return None

    text = ''.join(post)
    for i, month in enumerate(months):
        text = text.replace(month, ".%d" % (i + 1))
    result = [date for date in full_date_regex.findall(text.replace(' ', '')) if '.' in date]
    if result:
        for item in result:
            date = datetime_from_full_date(item)
            if date:
                return date

    result = short_date_regex.findall(text.replace(' ', ''))
    if result:
        for item in result:
            date = datetime_from_short_date(item)
            if date:
                return date

    result = [weekdays[word] for word in post if word in weekdays]
    if result:
        for item in result:
            date = datetime_from_weekday(item)
            if date:
                return date

    return None


def classifier(filename):
    current_date = datetime.datetime.now().date()
    with open(filename, 'r') as file_corpus:
        for post in file_corpus:
            try:
                if not post.strip():
                    continue
                post_id, publish_date, text = post.strip().split('\t')
                if model.classify(normalizer.normalize(text), args.alpha)[0] >= args.threshold:
                    date = parse_date(post=normalizer.mystem.lemmatize(text),
                                      publish_date=datetime.datetime.fromtimestamp(int(publish_date)).date())
                    if date and date > current_date:
                        contest = Contest(post_id, text, date, group[int(post_id.split('_')[0][1:])], [])
                        contest.save()
            except Exception as msg:
                print(msg)
    os.remove(filename)


def initializer():
    global model, normalizer, group, database
    model = NaiveBayesModel.load(args.model)
    group = GroupModel.load(args.group)
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
    global args, config
    # Парсинг аргументов командной строки
    args = parse_args()
    config = SourceFileLoader('*', 'server.conf').load_module()
    files = list(
        map(lambda x: "%s/%s" % (args.folder, x),
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
