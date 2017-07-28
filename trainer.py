import argparse
import gensim

from luckybot.model.naive_bayes import NaiveBayesModel


# Функция парсинга аргументов командной строки
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--accepted', type=str, default='accepted.corpus',
                        help='Filename with accepted documents')
    parser.add_argument('-r', '--rejected', type=str, default='rejected.corpus',
                        help='Filename with rejected documents')
    parser.add_argument('-o', '--output', type=str, default='objects/bayes.model',
                        help='Path to file with Naive Bayes model')
    parser.add_argument('--min_count', type=int, default=10,
                        help='The minimum count of times a bigram is to meet')
    parser.add_argument('--threshold', type=int, default=5,
                        help='Score threshold for forming the phrases (higher means fewer phrases)')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    bigram = gensim.models.Phrases([item.strip().split() for item in open(args.accepted, 'r') if item.strip()],
                                   min_count=args.min_count, threshold=args.threshold)
    model = NaiveBayesModel([args.accepted, args.rejected], bigram=bigram, bernoulli=True)
    model.save(args.output)
