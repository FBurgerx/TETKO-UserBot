# SPDX-License-Identifier: MIT
# Copyright (c) 2026 flexownerAL, @anhedonuya
# ---- meta data ----- ping ------------------------------
# authors: @flexownerAL, @anhedonuya
# description: Ping with adaptive TETKO logo (MCUB-style)
# ---- meta data end -------------------------------------
"""Ping — проверка связи с адаптивным логотипом."""
import time

from core.lib.loader.module_base import ModuleBase, command


# ─── 3 премиум-эмодзи, которые образуют логотип TETKO ───
TETKO_PREMIUM_LOGO = (
    '<tg-emoji emoji-id="5285530631567095762">🙏</tg-emoji>'
    '<tg-emoji emoji-id="5285030066013648645">📧</tg-emoji>'
    '<tg-emoji emoji-id="5285504668489785087">🅾️</tg-emoji>'
)


class Ping(ModuleBase):
    """Отвечает на .ping — проверка задержки."""

    name = "ping"
    version = "1.2.0"
    author = "@anhedonuya"
    description = {
        "ru": "Проверка связи с реальной задержкой",
        "en": "Check connection with real latency",
    }

    async def _get_logo(self) -> str:
        """Премиум-эмодзи для Premium-аккаунтов, иначе текст TETKO."""
        try:
            me = await self.kernel.client.get_me()
            if getattr(me, "premium", False):
                return TETKO_PREMIUM_LOGO
        except Exception:
            pass
        return "TETKO"

    @command("ping", doc={"ru": "проверить задержку", "en": "check latency"})
    async def cmd_ping(self, event):
        # Замеряем время от получения сообщения
        start = time.perf_counter()

        # Отправляем предварительный ответ
        msg = await event.reply("⏳ Считаю пинг...")
        round_trip = (time.perf_counter() - start) * 1000

        # Получаем логотип (премиум или текст)
        logo = await self._get_logo()

        # Второй замер — от отправки до редактирования
        edit_start = time.perf_counter()
        await msg.edit(
            f"<b>{logo} работает</b>\n"
            f"<b>⚡ Пинг:</b> <code>{round_trip:.0f} мс</code>"
        )
        edit_time = (time.perf_counter() - edit_start) * 1000

        # Итоговый пинг — среднее
        total = (round_trip + edit_time) / 2

        await msg.edit(
            f"<b>{logo} работает</b>\n"
            f"<b>⚡ Пинг:</b> <code>{total:.0f} мс</code>"
        )
