"""ModuleDispatcher — вызов native + MCUB команд."""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class DispatchResult:
    handled: bool = False
    value: Any = None
    error: Exception | None = None


class ModuleDispatcher:
    def __init__(self, registry, permissions=None, kernel=None):
        """
        registry — native-реестр (NativeRegistry)
        permissions — опционально
        kernel — StandardKernel (для доступа к command_handlers — MCUB)
        """
        self.registry = registry
        self.permissions = permissions
        self.kernel = kernel

    async def dispatch(self, message, command: str | None = None) -> DispatchResult:
        # ─── 1. NATIVE ───
        native_handlers = []
        if command:
            try:
                native_handlers = self.registry.find_handlers(command) or []
            except Exception:
                native_handlers = []
        else:
            try:
                native_handlers = self.registry.watchers() or []
            except Exception:
                native_handlers = []

        for spec in native_handlers:
            try:
                if self.permissions and not self.permissions.allowed(spec, message):
                    continue
                args = self._arguments(spec.callback, message)
                value = spec.callback(*args)
                if inspect.isawaitable(value):
                    value = await value
                return DispatchResult(True, value)
            except Exception as exc:
                return DispatchResult(True, error=exc)

        # ─── 2. MCUB / HIKKA (через kernel.command_handlers) ───
        if command and self.kernel is not None:
            result = await self._dispatch_mcub(message, command)
            if result.handled:
                return result

        return DispatchResult(False)

    async def _dispatch_mcub(self, message, command: str) -> DispatchResult:
        """Вызов MCUB-команды из kernel.command_handlers."""
        handlers = getattr(self.kernel, "command_handlers", None) or {}

        cmd_lower = command.lower()
        callback = handlers.get(cmd_lower)

        # Если нет в command_handlers — ищем в aliases
        if callback is None:
            aliases = getattr(self.kernel, "aliases", None) or {}
            real = aliases.get(cmd_lower)
            if real:
                callback = handlers.get(real)

        if callback is None:
            return DispatchResult(False)

        try:
            # MCUB-команды ожидают (event) или (self, event)
            value = callback(message)
            if inspect.isawaitable(value):
                value = await value
            return DispatchResult(True, value)
        except Exception as exc:
            return DispatchResult(True, error=exc)

    @staticmethod
    def _arguments(callback: Callable, message):
        try:
            params = list(inspect.signature(callback).parameters)
        except (TypeError, ValueError):
            return (message,)
        return (message,) if len(params) <= 1 else (message,)
