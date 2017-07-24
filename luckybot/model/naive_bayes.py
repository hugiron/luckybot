import math
import pickle


class NaiveBayesModel:
    def __init__(self, sample, bigram=None, bernoulli=False):
        self._bigram = bigram
        self._class_count = len(sample)
        self._count = [0] * self._class_count
        self._frequency = [0] * self._class_count
        self._vocab = dict()

        for class_index, filename in enumerate(sample):
            with open(filename, 'r') as corpus:
                for doc in corpus:
                    text = doc.strip().split()
                    if not text:
                        continue
                    if self._bigram:
                        text = self._bigram[text]
                    self._frequency[class_index] += 1
                    if bernoulli:
                        text = set(text)
                        self._count[class_index] += 1
                    else:
                        self._count[class_index] += len(text)
                    for word in text:
                        if word not in self._vocab:
                            self._vocab[word] = [0] * self._class_count
                        self._vocab[word][class_index] += 1
        self._frequency = [math.log(doc_count / sum(self._frequency)) for doc_count in self._frequency]

    def classify(self, text, alpha=1):
        def probability(class_index):
            try:
                return 1 / (1 + sum([math.exp(current[j] - current[class_index])
                                     for j in range(self._class_count) if class_index != j]))
            except:
                return 0

        text = self._bigram[text]
        current = [self._frequency[i] + sum([math.log(((self._vocab[word][i] if word in self._vocab else 0) + alpha) /
                                                      (alpha * len(self._vocab) + self._count[i]))
                                             for index, word in enumerate(text)]) for i in range(self._class_count)]
        return [probability(i) for i in range(self._class_count)]

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)
