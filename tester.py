import argparse

from luckybot.model.naive_bayes import NaiveBayesModel
from luckybot.util.normalizer import Normalizer


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--accepted', type=str, default='test_accepted.corpus',
                        help='Filename with test accepted documents')
    parser.add_argument('--rejected', type=str, default='test_rejected.corpus',
                        help='Filename with test rejected documents')
    parser.add_argument('-m', '--model', type=str, default='objects/bayes.model',
                        help='Path to file with Naive Bayes model')
    parser.add_argument('-a', '--alpha', type=float, default=1,
                        help='Value of function smoothing (0; +inf)')
    parser.add_argument('-t', '--threshold', type=float, default=0.95,
                        help='Activation function threshold [0; 1]')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    normalizer = Normalizer()
    model = NaiveBayesModel.load(args.model)

    accepted = [(normalizer.normalize(line.strip()), 1) for line in open(args.accepted, 'r') if line.strip()]
    rejected = [(normalizer.normalize(line.strip()), 0) for line in open(args.rejected, 'r') if line.strip()]
    accepted_count = len(accepted)
    sample = accepted + rejected
    del accepted, rejected

    def similar(text):
        return model.classify(text, args.alpha)

    def activate(value):
        return 1 if value[0] >= args.threshold else 0

    full_accuracy = 0
    target_accuracy = 0
    fullness = 0
    for item in sample:
        answer = activate(similar(item[0]))
        if answer and not ('{date}' in item[0] and ('{vk_url}' in item[0] or '{vk_group}' in item[0])):
            answer = 0
        if answer == item[1]:
            full_accuracy += 1
            target_accuracy += 1
            if item[1]:
                fullness += 1
        elif item[1]:
            target_accuracy += 1

    print('Absolute accuracy: %.2f%%' % (100 * full_accuracy / len(sample)))
    print('Relative accuracy: %.2f%%' % (100 * target_accuracy / len(sample)))
    print('Fullness of recognition: %.2f%%' % (100 * fullness / accepted_count))
