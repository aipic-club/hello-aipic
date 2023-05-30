
from enum import Enum
from typing import Any


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
    READY = 'READY'
    INTERACTION_CREATE = 'INTERACTION_CREATE'
    INTERACTION_SUCCESS = 'INTERACTION_SUCCESS'
    MESSAGE_CREATE = 'MESSAGE_CREATE'
    MESSAGE_ACK = 'MESSAGE_ACK'
    MESSAGE_DELETE = 'MESSAGE_DELETE'
    CHANNEL_UNREAD_UPDATE = 'CHANNEL_UNREAD_UPDATE'

    



browser = {
    "browser": "Chrome",
    "browser_user_agent":  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "browser_version": "113.0.0.0",
    "client_build_number": 199933,
    "device": "",
    "os": "Mac OS X",
    "os_version": "10.15.7"
}

MJBotId = 936929561302675456