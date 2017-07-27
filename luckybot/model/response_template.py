import json
import random


class ResponseTemplate:
    def __init__(self, templates):
        self.templates = templates

    def render(self, type, data=None):
        if type in self.templates:
            response = random.choice(self.templates[type]['text'])
            sticker = random.choice(self.templates[type]['sticker']) if 'sticker' in self.templates[type] else None
            if data:
                if isinstance(data, list):
                    data = '<br>'.join(map(str, data))
                return response.replace("{% data %}", data), sticker
            else:
                return response, sticker
        else:
            return None

    @staticmethod
    def load(filename):
        with open(filename, 'r') as file:
            return ResponseTemplate(json.load(file))
