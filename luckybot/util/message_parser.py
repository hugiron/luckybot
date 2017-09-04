from luckybot.util.normalizer import Normalizer
from luckybot.util.transliterator import translit


class MessageParser:
    def __init__(self, city, category):
        self.city = city
        self.category = category
        self.normalizer = Normalizer()

        self.grammar = dict(
            main=dict(
                next={'add', 'delete', 'help', 'contest', 'city', 'category', 'gift'}
            ),
            secondary=dict(
                next={'greeting', 'thanks'}
            ),
            thanks=dict(
                keywords={'spasibo', 'blagodarit', 'sposibo', 'thank', 'thanks', 'krasava', 'molodec', 'spasibochki',
                          'mersi', 'blagodarnost', 'blagodarstvovat', 'blagodarnyj', 'sesibon', 'sps', 'spasibok'}
            ),
            greeting=dict(
                keywords={'privet', 'privetulya', 'dratut', 'darof', 'zdravstvovat', 'jou', 'ku', 'start', 'startovat',
                          'nachinat', 'pognat', 'nachalo', 'privetstvovat', 'jo'}
            ),
            add=dict(
                keywords={'dobavlyat', 'vstavlyat', 'pribavlyat', 'prisoedinyat', 'otslezhivat', 'zakinut', 'sohranyat',
                          'podpisyvatsya', 'podpisyvat', 'podkljuchat', 'podkljuchatsya', 'nachinat'}
            ),
            delete=dict(
                keywords={'udal', 'ubirat', 'udalyat', 'steret', 'otstavlyat', 'otpisyvat', 'otpisyvatsya',
                          'otkljuchat', 'otkljuchatsya', 'perestavat', 'prekrashhat'}
            ),
            help=dict(
                keywords={'pomoshh', 'pomogat', 'instrukciya', 'help', 'komanda', 'funkciya', 'funkcional', 'umet'}
            ),
            contest=dict(
                keywords={'konkurs', 'rozygrysh', 'lotereya', 'halyava', 'halyavnyj', 'besplatnyj', 'besplatno',
                          'hotet', 'davat', 'razdavat', 'razygryvat', 'otdavat'}
            ),
            city=dict(
                keywords={'gorod', 'derevnya', 'muhosransk'}
            ),
            category=dict(
                keywords={'kategoriya', 'klass', 'razdel', 'tip'}
            ),
            gift=dict(
                keywords={'priz', 'dar', 'vyigrysh', 'nagrada', 'trofej', 'dobycha'}
            )
        )

    def search_city(self, text):
        return self.city[map(translit, text)]

    def search_category(self, text):
        return self.category[text]

    def search_gift(self, text):
        return [value for key, value in enumerate(text.replace('`', '"').replace('\'', '"').split('"')) if key % 2]

    def parse(self, message, user_id):
        current = 'main'
        message = self.normalizer.preprocess(message)
        command = list()
        lemms = self.normalizer.mystem.lemmatize(message)

        for i in range(len(lemms)):
            if not lemms[i].isalpha() or 'next' not in self.grammar[current]:
                continue
            lex = translit(lemms[i])

            for state in self.grammar[current]['next']:
                if lex in self.grammar[state]['keywords']:
                    command.append(state)
                    current = state
                    break

        result = dict(user_id=user_id, data=dict())

        if command:
            result['command'] = '_'.join(command)
        else:
            for key in self.grammar['secondary']['next']:
                if self.grammar[key]['keywords'].intersection(map(translit, lemms)):
                    result['command'] = key
                    break

        result['data']['city'] = self.search_city(self.normalizer.filter(lemms))
        if not result['data']['city']:
            del result['data']['city']
        result['data']['category'] = self.search_category(self.normalizer.filter(lemms))
        if not result['data']['category']:
            del result['data']['category']
        result['data']['gift'] = self.search_gift(message)
        if not result['data']['gift']:
            del result['data']['gift']

        if result['data'] and 'command' not in result:
            result['command'] = 'contest'

        if result.get('command') == 'contest':
            if 'city' not in result['data'] and self.grammar['city']['keywords'].intersection(lemms):
                result['data']['city'] = list()
            if 'category' not in result['data'] and self.grammar['category']['keywords'].intersection(lemms):
                result['data']['category'] = list()
            if 'gift' not in result['data'] and self.grammar['gift']['keywords'].intersection(lemms):
                result['data']['gift'] = list()

        return result
