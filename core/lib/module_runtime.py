"""Unified module metadata and translator reporting for TETKO."""
from __future__ import annotations


def translator_name(module=None, source: str = "", *, hikka: bool = False, library: bool = False) -> str:
    if library:
        return "hikka_compat"
    obj = getattr(module, "_class_instance", None) or module
    if hikka or getattr(obj, "_hikka_compat", False):
        return "hikka_compat"
    markers = ("from .. import loader", "from .. import utils", "@loader.tds", "loader.Module")
    if any(marker in source for marker in markers):
        return "mcub_compat_beta"
    return "native"


def translator_message(module=None, source: str = "", *, hikka: bool = False, library: bool = False) -> str:
    name = translator_name(module, source, hikka=hikka, library=library)
    if name == "native":
        return "This module was working in classic native non-translator."
    return f"This module was working in {name} translator."


def module_event(module, event: str, source: str = "", **flags) -> str:
    return f"[{event}] {getattr(module, 'name', type(module).__name__)} — {translator_message(module, source, **flags)}"
