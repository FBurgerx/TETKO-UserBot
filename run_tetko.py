# SPDX-License-Identifier: MIT
# Copyright (c) 2026 flexownerAL, @anhedonuya
# ---- meta data ----- run_tetko -------------------------
# authors: @flexownerAL, @anhedonuya
# description: TETKO entry point (StandardKernel, userbot)
# ---- meta data end -------------------------------------
"""Точка входа TETKO."""
import asyncio

from core.banner import print_banner
from core.version import __version__ as TETKO_VERSION
from core.kernel.standard import StandardKernel


async def main():
    # Баннер при запуске
    print_banner(version=TETKO_VERSION, codename="native+mcub")

    kernel = StandardKernel()
    try:
        # Стандартный запуск (native-путь)
        if hasattr(kernel, 'start') and hasattr(kernel, 'telegram'):
            await kernel.start()
            print(f"TETKO connected to Telegram (v{TETKO_VERSION})")
            print('Loaded modules:', ', '.join(getattr(kernel.loader, 'loaded', {}) or ['none']))
            await kernel.telegram.run_until_disconnected()
        else:
            # Полный путь через миксин (если реализован)
            await kernel.run()
    except KeyboardInterrupt:
        print("\n[!] Stopped by user")


if __name__ == '__main__':
    asyncio.run(main())
