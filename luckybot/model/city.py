import pickle


class CityModel:
    def __init__(self):
        self.id = None
        self.city = dict()

    def add(self, city, id):
        if not city:
            self.id = id
        else:
            if city[0] not in self.city:
                self.city[city[0]] = CityModel()
            self.city[city[0]].add(city[1:], id)

    def __getitem__(self, item):
        result = list()
        current = self
        for elem in item:
            if elem not in current.city:
                if current.id:
                    result.append(current.id)
                current = self
            if elem in current.city:
                current = current.city[elem]
        if current.id:
            result.append(current.id)
        return result

    @staticmethod
    def build(source):
        if isinstance(source, str):
            source = {city: int(line.split('\t')[0]) for line in open(source, 'r') if line.strip()
                      for city in line.strip().split('\t')[1].split('|')}
        current = CityModel()
        for city, id in source.items():
            current.add(city.split(), id)
        return current

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)
