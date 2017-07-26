import re
import nltk
from pymystem3 import Mystem


class Normalizer:
    def __init__(self):
        vk_url = r'(https?:\/\/)?vk\.com\/[\d\w\.\_]+'
        vk_group = r'\[club\d+\|[^\]]+\]'
        vk_user = r'\[id\d+\|[^\]]+\]'
        url = r'(https?:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'
        tag = r'#[^\s]+'
        date = r'(\d{1,2}\.\d{1,2}(\.\d{2,4})?)|(\d{1,2}\s+' \
               r'(январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь))|' \
               r'(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)'

        self.vk_url_regex = re.compile(vk_url)
        self.vk_group_regex = re.compile(vk_group)
        self.vk_user_regex = re.compile(vk_user)
        self.url_regex = re.compile(url)
        self.date_regex = re.compile(date)
        self.regex = re.compile('(%s)|(%s)|(%s)|(%s)' % (vk_group, vk_user, url, tag))

        self.stopwords = set(nltk.corpus.stopwords.words('russian'))
        self.mystem = Mystem()

        self.replace_set = [
            ("<br>", " "),
            ("\n", " "),
            ("й", "и"),
            ("ё", "е")
        ]

    def normalize(self, text):
        text = self.preprocess(text)
        vk_url_count = len(self.vk_url_regex.findall(text))
        vk_group_count = len(self.vk_group_regex.findall(text))
        vk_user_count = len(self.vk_user_regex.findall(text))
        url_count = len(self.url_regex.findall(text)) - vk_url_count
        text = ' '.join(self.mystem.lemmatize(self.regex.sub(" ", self.preprocess(text))))
        date_count = len(self.date_regex.findall(text))
        return self.filter(text.split()) + ['{vk_group}'] * vk_group_count + ['{vk_user}'] * vk_user_count + \
               ['{date}'] * date_count + ['{vk_url}'] * vk_url_count + ['{url}'] * url_count

    def preprocess(self, text):
        text = text.lower()
        for item in self.replace_set:
            text = text.replace(item[0], item[1])
        return text

    def filter(self, lemms):
        return [lemm for lemm in lemms if lemm not in self.stopwords and lemm.isalpha() and len(lemm) > 1]
