import json
from functools import reduce


class CategoryModel:
    def __init__(self, data):
        self.vocab = dict()
        self.keywords = dict()
        self.categories = list()
        for first in data:
            data[first]['tags'] = set(data[first]['tags'])
            self.categories.append((0, first, data[first]['title']))
            self.keywords[first] = set(data[first]['keywords'])
            for word in data[first]['tags']:
                if word not in self.vocab:
                    self.vocab[word] = list()
                self.vocab[word].append(first)
            if 'child' in data[first]:
                for second in data[first]['child']:
                    category_id = "%s:%s" % (first, second)
                    data[first]['child'][second]['tags'] = set(data[first]['child'][second]['tags'])
                    self.categories.append((1, category_id, data[first]['child'][second]['title']))
                    self.keywords[category_id] = set(data[first]['child'][second]['keywords'])
                    self.keywords[first] = self.keywords[first].union(self.keywords[category_id])
                    for word in data[first]['child'][second]['tags']:
                        if word not in self.vocab:
                            self.vocab[word] = list()
                        self.vocab[word].append(category_id)
        self.data = data

    def __getitem__(self, sentence):
        if isinstance(sentence, str):
            sentence = sentence.split()
        sentence = [word for word in sentence if word in self.vocab]
        norm_sentence = [self.vocab[word] for word in sentence]

        def check_seq(seq):
            if not seq:
                return False
            if ':' in seq[0]:
                seq.reverse()
            first = [index + 1 for index, item in enumerate(seq) if ':' not in item]
            second = [index + 1 for index, item in enumerate(seq) if ':' in item]
            return (reduce(lambda x, y: y if y == x + 1 and x else 0, first) if first else True) and \
                   (reduce(lambda x, y: y if y == x + 1 and x else 0, second) if second else True)

        def parse(accumulator, balance):
            if balance:
                seq = list()
                for option in balance[0]:
                    seq.append(parse(accumulator + [option], balance[1:]))
                maximum = max(seq, key=lambda x: x[1])[1]
                return min(filter(lambda x: x[1] == maximum, seq), key=lambda x: len(x[0]))
            else:
                result = set()
                result_lexem = 0
                current = list()
                key = None
                for category in accumulator:
                    last_key = category.split(':')[0]
                    if key != last_key:
                        #if key in current and check_seq(current):
                        if check_seq(current):
                            result_lexem += len(current)
                            current.remove(key)
                            if current:
                                result = result.union(current)
                            else:
                                result.add(key)
                        key = last_key
                        current = list()
                    current.append(category)
                #if key in current and check_seq(current):
                if check_seq(current):
                    result_lexem += len(current)
                    current.remove(key)
                    if current:
                        result = result.union(current)
                    else:
                        result.add(key)
                return list(result), result_lexem

        return parse([], norm_sentence)[0]

    def get_keywords(self, category_id):
        if isinstance(category_id, str):
            return list(self.keywords[category_id])
        elif isinstance(category_id, list):
            return list(reduce(lambda x, y: x.union(y), map(lambda x: self.keywords[x], category_id)))

    def get_categories(self, current_categories=None):
        if isinstance(current_categories, list):
            current_categories = set(current_categories)
        category_list = list()
        for category in self.categories:
            category_list.append("%s %s [%s]" % (('' if category[0] else '<br>') + '•' * category[0],
                                                category[2],
                                                '+' if category[1].split(':')[0] in current_categories or
                                                       category[1] in current_categories else '-'))
        return category_list

    @staticmethod
    def load(filename):
        with open(filename, 'r') as file:
            return CategoryModel(json.load(file))
