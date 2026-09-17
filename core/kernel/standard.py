# SPDX-License-Identifier: MIT
# Copyright (c) 2026 flexownerAL, @anhedonuya
# ---- meta data ----- standard --------------------------
# authors: @flexownerAL, @anhedonuya
# description: Standard kernel - full build (mcub + hikka + native)
# ---- meta data end -------------------------------------
"""StandardKernel — полное ядро TETKO, собирающее все миксины."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

# ---- Core mixins ----
from core.lib.kernel_core import KernelCoreMixin
from core.lib.kernel_handlers import KernelHandlersMixin
from core.lib.kernel_lifecycle import KernelLifecycleMixin
from core.lib.kernel_pipeline import KernelPipelineMixin

# ---- Loaders ----
from core.loader import NativeLoader

# ---- Context ----
from core.subcores.context import KernelContext


log = logging.getLogger("TETKO.kernel")


class StandardKernel(
    KernelCoreMixin,
    KernelHandlersMixin,
    KernelLifecycleMixin,
    KernelPipelineMixin,
):
    """
    Стандартное ядро TETKO.

    Наследует:
      • KernelCoreMixin     — config, register, db, paths, cache
      • KernelHandlersMixin — command_handlers, watchers, callbacks, inline
      • KernelLifecycleMixin — run, stop, shutdown, restart
      • KernelPipelineMixin  — pipeline, regex, scripts

    Плюс:
      • NativeLoader — для native-модулей (наследников NativeModule)
    """

    def __init__(self) -> None:
        super().__init__()

        # ---- Context для native-части ----
        self.context = KernelContext()
        self.context.registry = self.loaded_modules

        # ---- Native loader ----
        try:
            self.native_loader = NativeLoader(self.loaded_modules, self.context)
        except Exception as e:
            log.warning(f"NativeLoader init failed: {e}")
            self.native_loader = None

        # ---- ModuleLoader (MCUB/Hikka) ----
        try:
            from core.lib.loader.loader import ModuleLoader
            self.module_loader = ModuleLoader(self)
        except Exception as e:
            log.warning(f"ModuleLoader init failed: {e}")
            self.module_loader = None

        # ---- Telegram service (для нашего упрощённого пути) ----
        try:
            from core.telegram import TelegramClientService
            self.telegram = TelegramClientService(self.context)
        except Exception as e:
            log.debug(f"TelegramClientService init failed: {e}")
            self.telegram = None

        self.started = False
        log.debug("[StandardKernel] __init__ done")


# Алиас для совместимости
Kernel = StandardKernel
