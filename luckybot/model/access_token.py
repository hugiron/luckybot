import json
import random


class AccessToken:
    def __init__(self, filename):
        with open(filename, 'r') as file:
            self._access_token = json.load(file)

    def __call__(self, *args, **kwargs):
        return random.choice(self._access_token)
