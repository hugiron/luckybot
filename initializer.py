# Download stopwords for NLTK
import nltk.downloader
loader = nltk.downloader.Downloader('http://nltk.github.com/nltk_data/')
loader.download('stopwords')

from nltk.corpus import stopwords
set_stopwords = set(stopwords.words('russian'))

# Download Mystem for pymystem3
from pymystem3 import Mystem
mystem = Mystem()

# Create collections and indexes in database (Contest and User models)
from importlib.machinery import SourceFileLoader
from mongoengine import connect
from luckybot.model.contest import Contest
from luckybot.model.user import User

config = SourceFileLoader('*', 'server.conf').load_module()
database = connect(db=config.mongo_database, host=config.mongo_host, port=int(config.mongo_port),
                       username=config.mongo_username, password=config.mongo_password)
contest_count = Contest.objects.count()
user_count = User.objects.count()

# Creating working directories
import os

os.mkdir('data')
os.mkdir('log')
