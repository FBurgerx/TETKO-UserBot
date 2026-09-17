from dataclasses import dataclass, field
from typing import Any, Callable, Tuple

@dataclass(frozen=True)
class HandlerSpec:
    kind: str
    name: str
    callback: Callable[..., Any]
    aliases: Tuple[str, ...] = field(default_factory=tuple)
    priority: int = 0
    owner_only: bool = False


def _mark(kind, name=None, aliases=(), priority=0, owner_only=False):
    def deco(fn):
        spec = HandlerSpec(kind, name or fn.__name__, fn, tuple(aliases), priority, owner_only)
        setattr(fn, "__tetko_handler__", spec)
        return fn
    return deco


def command(name=None, *aliases, priority=0, owner_only=False):
    return _mark("command", name, aliases, priority, owner_only)


def watcher(priority=0):
    return _mark("watcher", priority=priority)


def callback(name=None, *aliases, priority=0):
    return _mark("callback", name, aliases, priority)


def loop(name=None, priority=0):
    return _mark("loop", name, priority=priority)
