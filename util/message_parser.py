from util.transliterator import translit
from util.normalizer import Normalizer
from model.recv_message import RecvMessage


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
                          'nahodit', 'poisk', 'iskat', 'rasskazyvat', 'podelitsya'},
                next={'contest'}
            ),
            add=dict(
                keywords={'dobavlyat', 'vstavlyat', 'pribavlyat', 'prisoedinyat', 'otslezhivat'}
            ),
            delete=dict(
                keywords={'udal', 'ubirat', 'udalyat', 'steret', 'otstavlyat'}
            ),
            help=dict(
                keywords={'pomoshh', 'pomogat', 'instrukciya', 'help', 'komanda', 'funkciya', 'funkcional', 'umet'}
            ),
            contest=dict(
                keywords={'konkurs', 'rozygrysh', 'lotereya'}
            ),
            city=dict(
                keywords={'gorod', 'derevnya'},
                remainder=self.remainder_city
            ),
            category=dict(
                keywords={'kategoriya', 'klass', 'razdel', 'tip'},
                remainder=self.remainder_category
            ),
            gift=dict(
                keywords={'podarok', 'priz', 'dar', 'vyigrysh', 'nagrada', 'trofej', 'dobycha'},
                remainder=self.remainder_gift
            )
        )

    def is_city(self, lex):
        return lex in self.city

    def is_category(self, lex):
        return lex in self.category

    def remainder_city(self, text):
        return [self.city[lex] for lex in map(translit, self.normalizer.normalize(text)) if lex in self.city]

    def remainder_category(self, text):
        return [self.category[lex] for lex in map(translit, self.normalizer.normalize(text)) if lex in self.category]

    def remainder_gift(self, text):
        return [value for key, value in enumerate(text.replace('`', '"').replace('\'', '"').split('"')) if key % 2]

    def parse(self, message, user_id):
        current = 'main'
        message = message.lower().replace("<br>", " ").replace("\n", " ")
        command = list()
        lemms = self.normalizer.mystem.lemmatize(message)
        target = None

        for i in range(len(lemms)):
            if not lemms[i].isalpha():
                continue
            lex = translit(lemms[i])
            if not target and (self.is_city(lex) or lex in self.grammar['city']['keywords']):
                target = 'city'
            elif not target and (self.is_category(lex) or lex in self.grammar['category']['keywords']):
                target = 'category'
            elif not target and lex in self.grammar['gift']['keywords']:
                target = 'gift'
            elif 'next' in self.grammar[current]:
                for state in self.grammar[current]['next']:
                    if lex in self.grammar[state]['keywords']:
                        command.append(state)
                        current = state
                        break
        if target and 'help' not in command:
            command.append(target)

        result = dict(user_id=user_id)
        if command:
            result['command'] = '_'.join(command)
        if target and 'remainder' in self.grammar[target]:
            result['data'] = self.grammar[target]['remainder'](message)
        return RecvMessage.from_json(result)
