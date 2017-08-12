import json


class CityModel:
    def __init__(self, title=None):
        self.id = None
        self.city = dict()
        self.title = title

    def add(self, city, id):
        if not city:
            self.id = id
        else:
            if city[0] not in self.city:
                self.city[city[0]] = CityModel()
            self.city[city[0]].add(city[1:], id)

    def get_title(self, id):
        return self.title.get(id)

    def exist(self, id):
        return id in self.title

    def __getitem__(self, item):
        result = set()
        current = self
        for elem in item:
            if elem not in current.city:
                if current.id:
                    result.add(current.id)
                current = self
            if elem in current.city:
                current = current.city[elem]
        if current.id:
            result.add(current.id)
        return list(result)

    @staticmethod
    def load(filename):
        with open(filename, 'r') as file:
            cities = json.load(file)
        title = {city['id']: city['title'] for city in cities}
        source = {tag: city['id'] for city in cities for tag in city['tags']}
        current = CityModel(title)
        for city, id in source.items():
            current.add(city.split(), id)
        return current
