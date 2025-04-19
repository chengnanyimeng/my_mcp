from dataclasses import dataclass
from typing import Any

@dataclass
class Event:
    event: str
    data: Any
