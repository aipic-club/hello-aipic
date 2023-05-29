
from enum import Enum


class Enum(Enum):
    def __str__(self) -> str:
        return self.name
    def __repr__(self) -> str:
        return self.name

class Opcodes(Enum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11


class Events(Enum):
    INTERACTION_CREATE = 'INTERACTION_CREATE',
    INTERACTION_SUCCESS = 'INTERACTION_SUCCESS',
