from luckybot.util.normalizer import Normalizer
from luckybot.util.transliterator import translit


class MessageParser:
    def __init__(self, city, category):
        self.city = city
        self.category = category
        self.normalizer = Normalizer()

        self.grammar = dict(
            main=dict(
                next={'show', 'add', 'delete', 'help'}
            ),
            show=dict(
                keywords={'pokazyvat', 'poluchat', 'napisat', 'davat', 'posmotret', 'prosmatrivat', 'prosmotr',
                          'nahodit', 'poisk', 'iskat', 'rasskazyvat', 'podelitsya', 'daya', 'prihodit', 'naidi',
                          'prisylat'},
                next={'contest', 'city', 'category', 'gift'}
            ),
            add=dict(
                keywords={'dobavlyat', 'vstavlyat', 'pribavlyat', 'prisoedinyat', 'otslezhivat', 'zakinut', 'sohranyat'}
            ),
            delete=dict(
                keywords={'udal', 'ubirat', 'udalyat', 'steret', 'otstavlyat'}
            ),
            help=dict(
                keywords={'pomoshh', 'pomogat', 'instrukciya', 'help', 'komanda', 'funkciya', 'funkcional', 'umet'}
            ),
            contest=dict(
                keywords={'konkurs', 'rozygrysh', 'lotereya', 'halyava'},
                next={'city', 'category', 'gift'}
            ),
            city=dict(
                keywords={'gorod', 'derevnya', 'muhosransk'}
            ),
            category=dict(
                keywords={'kategoriya', 'klass', 'razdel', 'tip'}
            ),
            gift=dict(
                keywords={'podarok', 'priz', 'dar', 'vyigrysh', 'nagrada', 'trofej', 'dobycha'}
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

        data = self.search_city(self.normalizer.filter(lemms))
        if data:
            target = 'city'
        else:
            data = self.search_category(self.normalizer.filter(lemms))
            if data:
                target = 'category'
            else:
                data = self.search_gift(message)
                if data:
                    target = 'gift'
                else:
                    target = None

        result = dict(user_id=user_id)
        if command:
            if target and (command[0] == 'add' or command[0] == 'delete'):
                command.append(target)
            else:
                target = None
            result['command'] = '_'.join(command)
        if data:
            result['data'] = {target: data} if target else data

        return result
