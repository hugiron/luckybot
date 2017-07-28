import pickle


class GroupModel:
    def __init__(self):
        self.data = dict()

    def __setitem__(self, key, value):
        if value:
            self.data[key] = value

    def __getitem__(self, item):
        return self.data[item] if item in self.data else []

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)
