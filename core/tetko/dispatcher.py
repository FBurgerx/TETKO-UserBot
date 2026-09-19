"""Dispatcher — обработчик входящих событий Telegram для TETKO."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from telethon import errors

from core.tetko.context import Context
from core.tetko.registry import Registry

log = logging.getLogger("TETKO.tetko.dispatcher")


class EventDispatcher:
    """Диспетчер команд, ватчеров и колбэков."""

    def __init__(
        self,
        registry: Registry,
        prefix: str = ".",
        context: Optional[Context] = None,
    ):
        self.registry = registry
        self.prefix = prefix
        self.context = context

    def _check_access(self, only_for: Optional[str], user_id: Optional[int]) -> bool:
        """Проверка прав на команду.

        only_for=None     — всем
        only_for="owner"  — только владелец
        only_for="trusted" — владелец + доверенные
        """
        if self.context is None:
            return True
        if only_for == "owner":
            return self.context.is_owner(user_id)
        if only_for == "trusted":
            return self.context.is_trusted(user_id)
        return True

    async def _notify(self, client: Any, event: Any, text: str) -> None:
        """Ответить пользователю.

        event.edit() работает только для собственных сообщений владельца.
        Если команду прислал кто-то другой — edit молча падает и бот
        кажется «немым». Поэтому: владелец → edit, остальные → новое
        сообщение (reply).
        """
        from_id = getattr(event, "sender_id", None)
        owner_id = getattr(self.context, "admin_id", None) if self.context else None
        is_own = (
            from_id is not None
            and owner_id is not None
            and int(from_id) == int(owner_id)
        )
        if is_own:
            try:
                await event.edit(text, parse_mode="html")
                return
            except Exception:
                pass
        try:
            await client.send_message(
                event.chat_id, text, parse_mode="html", reply_to=event.id
            )
        except Exception:
            pass

    async def handle_message(self, client: Any, event: Any) -> None:
        """Обработка входящих сообщений Telegram."""
        text = getattr(event, "raw_text", "") or ""

        # 1. Команды (начинаются с префикса)
        if text.startswith(self.prefix):
            body = text[len(self.prefix):]
            parts = body.split(maxsplit=1)
            if parts:
                cmd_name = parts[0].lower()
                cmd_args = parts[1].split() if len(parts) > 1 else []

                command = self.registry.find_command(cmd_name)
                if command:
                    # ── Проверка прав ──
                    if command.only_for:
                        sender_id = getattr(event, "sender_id", None)
                        if self.context is None or not self._check_access(
                            command.only_for, sender_id
                        ):
                            label = {
                                "owner": "только для владельца",
                                "trusted": "только для доверенных",
                            }.get(command.only_for, command.only_for)
                            await self._notify(
                                client, event, f"🚫 Эта команда {label}."
                            )
                            return

                    try:
                        # Прокидываем client в модуль
                        if hasattr(command.module, "client"):
                            try:
                                command.module.client = client
                            except Exception:
                                pass

                        await command.call(client, event, cmd_args)
                    except errors.FloodWaitError as fw:
                        # Telegram просит подождать — подчиняемся, а не падаем.
                        # Иначе юзербот умирает от блокировки аккаунта.
                        wait = min(fw.seconds, 600)
                        log.warning(
                            f"⏳ FloodWait {fw.seconds}s на команде .{cmd_name}; "
                            f"спим {wait}s"
                        )
                        await self._notify(
                            client,
                            event,
                            f"⏳ Telegram просит подождать <code>{fw.seconds}s</code>. "
                            f"Команда выполнится после.",
                        )
                        await asyncio.sleep(wait)
                    except Exception as e:
                        log.exception(f"Ошибка выполнения команды .{cmd_name}")
                        await self._notify(
                            client,
                            event,
                            f"❌ Ошибка в команде <code>.{cmd_name}</code>:\n<code>{e}</code>",
                        )
                    return

        # 2. Watchers
        for module, watcher_func in self.registry.list_watchers():
            try:
                await watcher_func(event)
            except Exception as e:
                log.exception(f"Ошибка ватчера в модуле {module.name}: {e}")

    async def handle_callback(self, client: Any, event: Any) -> None:
        """Обработка inline-кнопок (callback query).

        Приоритет:
          1. Временные хендлеры kernel.inline (make_button/form).
          2. Модульные @callback-хендлеры.
        """
        data = getattr(event, "data", b"") or b""
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")

        kernel = getattr(client, "kernel", None)
        if kernel is not None and hasattr(kernel, "inline"):
            h = kernel.inline.get_handler(data)
            if h is not None:
                func = h["func"]
                args = h["args"]
                try:
                    await func(event, *args)
                except Exception as e:
                    log.exception(f"Ошибка inline-хендлера: {e}")
                return

        for module, callback_func in self.registry.list_callbacks():
            try:
                await callback_func(event)
            except Exception as e:
                log.exception(f"Ошибка callback в модуле {module.name}: {e}")
