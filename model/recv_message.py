import json


class RecvMessage:
    def __init__(self, command, user_id, data):
        self.command = command
        self.user_id = user_id
        self.data = data

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(data):
        if isinstance(data, str):
            return RecvMessage(**json.loads(data))
        elif isinstance(data, dict):
            return RecvMessage(**data)
