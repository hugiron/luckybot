import sys
import json
import random


class ResponseTemplate:
    def __init__(self, templates):
        self.templates = templates

    def render(self, type, data=None):
        def choice(array):
            return array[random.randint(0, sys.maxsize) % len(array)]

        if type in self.templates:
            response = choice(self.templates[type]['text'])
            sticker = choice(self.templates[type]['sticker']) if 'sticker' in self.templates[type] else None
            if data:
                if isinstance(data, list):
                    data = '<br>'.join(map(str, data))
                return response.replace("{% data %}", data), sticker
            else:
                return response.replace("{% data %}", ''), sticker
        return None

    def get_text(self, type):
        if type in self.templates:
            return random.choice(self.templates[type]['text'])
        return None

    @staticmethod
    def load(filename):
        with open(filename, 'r') as file:
            return ResponseTemplate(json.load(file))
