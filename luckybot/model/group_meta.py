import pickle


class GroupMeta:
    def __init__(self):
        self.group_id = set()
        self.screen_name = set()

    def add(self, group_id, screen_name):
        self.group_id.add(group_id)
        if screen_name:
            self.screen_name.add(screen_name)

    def is_group(self, screen_name):
        return screen_name in self.screen_name

    def is_approved(self, group_id):
        return group_id in self.group_id

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self, file)

    @staticmethod
    def load(filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)
