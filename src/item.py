class Item:
    def __init__(self):
        self.range = None
        self.location = None
        self.type = None
        self.button = None
        self.hotkey = None
        self.interval = None
        self.clicks = None
        self.status = None

    def from_dict(self, dict):
        self.__dict__ = dict
        return self

    def to_dict(self):
        return self.__dict__

    def to_tuple(self):
        # return tuple(self.__dict__.values())
        return tuple(value if value != -1 else '--' for value in self.__dict__.values())