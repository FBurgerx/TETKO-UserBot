from dataclasses import dataclass, field
from typing import Any

@dataclass
class KernelContext:
    client: Any = None
    config: Any = None
    database: Any = None
    registry: Any = None
    dispatchers: Any = None
    services: dict = field(default_factory=dict)
    state: str = "created"
