from dataclasses import dataclass, field, fields


@dataclass
class Event:
    type: str = 'Click'
    hotkey: str = ''
    button: str = 'mouse_left'
    range: str = '*'
    position: list = field(default_factory=lambda: [-1, -1])
    interval: int = None
    clicks: int = None
    status: int = 1

    @property
    def posX(self) -> int:
        if isinstance(self.position, (list, tuple)) and len(self.position) >= 1:
            return self.position[0]
        return -1

    @property
    def posY(self) -> int:
        if isinstance(self.position, (list, tuple)) and len(self.position) >= 2:
            return self.position[1]
        return -1

    @property
    def isEnabled(self) -> bool:
        return self.status == 1

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


@dataclass
class Settings:
    enable_tray: bool = False
    startup: bool = False
    startup_as_admin: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'Settings':
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
