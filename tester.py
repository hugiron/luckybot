import argparse

from luckybot.model.naive_bayes import NaiveBayesModel
from luckybot.model.group_meta import GroupMeta
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
    parser.add_argument('--group_meta', type=str, default='objects/group_meta.model',
                        help='Path to model with approved groups and screen names')
    parser.add_argument('-a', '--alpha', type=float, default=0.01,
                        help='Value of function smoothing (0; +inf)')
    parser.add_argument('-t', '--threshold', type=float, default=0.9,
                        help='Activation function threshold [0; 1]')
    return parser.parse_args()


def validate_vk_url(vk_url):
    name = vk_url.split('/')[-1]
    if name.startswith('id') and name[2:].isdigit():
        return '{vk_user}'
    elif name.startswith('club') and name[4:].isdigit() or group_meta.is_group(name):
        return '{vk_group}'
    return '{vk_url}'


if __name__ == '__main__':
    global group_meta
    args = parse_args()
    normalizer = Normalizer()
    model = NaiveBayesModel.load(args.model)
    group_meta = GroupMeta.load(args.group_meta)

    # Accepted posts
    # [0] - post_id
    # [1] - text
    # [2] - class number
    accepted = [(int(line.strip().split('\t')[0].split('_')[0][1:]),
                 normalizer.normalize(line.strip().split('\t')[1], validate_vk_url),
                 1) for line in open(args.accepted, 'r') if line.strip()]
    # Rejected posts
    # [0] - post_id
    # [1] - text
    # [2] - class number
    rejected = [(int(line.strip().split('\t')[0].split('_')[0][1:]),
                 normalizer.normalize(line.strip().split('\t')[1], validate_vk_url),
                 0) for line in open(args.rejected, 'r') if line.strip()]
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
        answer = activate(similar(item[1]))
        if answer and (not group_meta.is_approved(item[0]) or '{date}' not in item[1]
                       or '{vk_group}' not in item[1] or '{url}' in item[1] or '{vk_user}' in item[1]):
            answer = 0
        if answer == item[2]:
            full_accuracy += 1
            target_accuracy += 1
            if item[2]:
                fullness += 1
        elif item[2]:
            target_accuracy += 1

    print('Absolute accuracy: %.2f%%' % (100 * full_accuracy / len(sample)))
    print('Relative accuracy: %.2f%%' % (100 * target_accuracy / len(sample)))
    print('Fullness of recognition: %.2f%%' % (100 * fullness / accepted_count))
