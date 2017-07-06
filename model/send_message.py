import json


class SendMessage:
    def __init__(self, type, user_id, data):
        self.type = type
        self.user_id = user_id
        self.data = data

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(data):
        if isinstance(data, str):
            return SendMessage(**json.loads(data))
        elif isinstance(data, dict):
            return SendMessage(**data)
