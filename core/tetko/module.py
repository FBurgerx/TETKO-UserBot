"""Module — базовый класс TETKO-модуля."""
from __future__ import annotations

import logging
from typing import Any, Optional

from core.tetko.config import ModuleConfig


class Module:
    """Базовый класс модуля TETKO."""

    name: str = "Unnamed"
    version: str = "0.0.0"
    author: str = "unknown"
    description: dict[str, str] = {}
    config: dict[str, Any] = {}

    def __init__(self, kernel: Optional[Any] = None):
        self.kernel = kernel
        self._config = ModuleConfig(self.name, self.config)
        self._logger = logging.getLogger(f"TETKO.module.{self.name}")
        self._loaded = False

    @property
    def cfg(self) -> ModuleConfig:
        return self._config

    @property
    def log(self) -> logging.Logger:
        return self._logger

    @property
    def client(self):
        if self.kernel and hasattr(self.kernel, "client"):
            return self.kernel.client
        return None

    async def on_load(self) -> None:
        pass

    # ─── Ответы ───
    async def respond(self, event, text: str, parse_mode=None):
        """Универсальный ответ на команду.

        Юзербот отвечает через event.edit() — но отредактировать можно
        только своё сообщение. Если команду прислал другой пользователь,
        edit() молча падает, и ответ никто не видит: кажется, что бот
        «молчит».

        Метод сам решает:
          - владелец → edit (классическое поведение юзербота)
          - другой пользователь → send_message новым сообщением
        """
        from_id = getattr(event, "sender_id", None)
        owner_id = None
        if self.kernel is not None:
            ctx = getattr(self.kernel, "context", None)
            if ctx is not None:
                owner_id = getattr(ctx, "admin_id", None)

        is_own = (
            from_id is not None
            and owner_id is not None
            and int(from_id) == int(owner_id)
        )

        if is_own:
            try:
                return await event.edit(text, parse_mode=parse_mode)
            except Exception:
                pass

        chat_id = getattr(event, "chat_id", None)
        reply_to = getattr(event, "id", None)
        client = self.client
        if client is None:
            return None
        try:
            return await client.send_message(
                chat_id, text, parse_mode=parse_mode, reply_to=reply_to
            )
        except Exception as e:
            self._logger.warning(f"respond: не удалось отправить ответ: {e}")
            return None

    async def on_unload(self) -> None:
        pass

    def get_description(self, lang: str = "ru") -> str:
        if isinstance(self.description, dict):
            return (
                self.description.get(lang)
                or self.description.get("en")
                or self.description.get("ru")
                or ""
            )
        return str(self.description)

    def __repr__(self) -> str:
        return f"<Module {self.name} v{self.version} by {self.author}>"
