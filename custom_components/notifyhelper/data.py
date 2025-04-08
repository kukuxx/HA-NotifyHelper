from dataclasses import dataclass, field
from typing import Deque
from collections import deque

@dataclass
class NotificationData:
    maxlen: int = 500
    messages: Deque[str] = field(init=False)
    badge: int = 0

    def __post_init__(self):
        self.messages = deque(maxlen=self.maxlen)

    def add_message(self, message: str, newbadge: int):
        self.messages.appendleft(message)
        self.badge = newbadge
        return {
            "msg": list(self.messages),
            "badge": self.badge,
        }

    def read_messages(self):
        read = [
            msg.replace("alert-type='info'", "alert-type='success'")
            if "alert-type='info'" in msg else msg
            for msg in self.messages
        ]
        self.messages.clear()
        self.messages.extend(read)
        self.badge = 0
        return {
            "msg": read,
            "badge": self.badge,
        }

    def clear_messages(self):
        self.messages.clear()
        self.badge = 0
        return {
            "msg": [],
            "badge": self.badge,
        }
    
    def from_dict(self, data: dict):
        self.messages.extend(data["msg"])
        self.badge = data["badge"]
