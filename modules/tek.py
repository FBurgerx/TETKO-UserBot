# SPDX-License-Identifier: MIT
# Copyright (c) 2026 flexOwnerAL | @flexOwnerAL

from __future__ import annotations

import ast
import asyncio
import contextlib
import html
import inspect
import json
import os
import traceback
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from telethon import events
from telethon.errors import BadRequestError
from telethon.tl.types import InputMediaWebPage

import utils
from core.lib.loader.module_base import ModuleBase, command
from core.lib.loader.module_config import Boolean, ConfigValue, Integer, ModuleConfig, String
from utils.strings import Strings


CUSTOM_EMOJI = {
    "crystal": '<tg-emoji emoji-id="5332762073388578651">🎮</tg-emoji>',
    "dna": '<tg-emoji emoji-id="5332762073388578651">❔</tg-emoji>',
    "alembic": '<tg-emoji emoji-id="5411243692960810848">🤔</tg-emoji>',
    "snowflake": '<tg-emoji emoji-id="5431895003821513760">❄️</tg-emoji>',
    "blocked": '<tg-emoji emoji-id="5332439413970469607">🚫</tg-emoji>',
    "pancake": '<tg-emoji emoji-id="5303396278179210513">👾</tg-emoji>',
    "confused": '<tg-emoji emoji-id="5408830797513784663">❓</tg-emoji>',
    "map": '<tg-emoji emoji-id="5332373172689860602">🚫</tg-emoji>',
    "tot": '<tg-emoji emoji-id="5404696015318054899">▪️</tg-emoji>',
    "eye_off": '<tg-emoji emoji-id="5228686859663585439">👁</tg-emoji>',
    "bot": '<tg-emoji emoji-id="5372981976804366741">🤖</tg-emoji>',
}

ZERO_WIDTH_CHAR = "\u2060"
MAN_MODULES_PER_PAGE_DEFAULT = 10
MAN_MODULES_PER_PAGE_MIN = 1
MAN_MODULES_PER_PAGE_MAX = 50

_METADATA_CACHE: dict[str, tuple[float, dict]] = {}
_METADATA_LOCKS: dict[int, asyncio.Lock] = {}


def _get_metadata_lock() -> asyncio.Lock:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.Lock()
    loop_id = id(loop)
    lock = _METADATA_LOCKS.get(loop_id)
    if lock is None:
        lock = asyncio.Lock()
        _METADATA_LOCKS[loop_id] = lock
    return lock


class TekModule(ModuleBase):
    """TETKO module manager with the original MCUB/Man customization.

    The MCUB customization layer is kept: banner/media, invert mode, custom
    emoji, module-per-page, hidden modules, metadata, aliases, config info and
    module-style detection.  Only the inline bot itself is intentionally gone.
    """

    name = "tek"
    version = "3.0.0"
    author = "@flexOwnerAL"
    description = {
        "ru": "Список модулей и их описание в стиле MCUB Man",
        "uk": "Список модулів та їх опис у стилі MCUB Man",
        "en": "Module list and descriptions with MCUB Man customization",
    }

    strings: dict | Strings = {
        "name": "Tek",
        "ru": {
            "system_modules": "Системные модули",
            "user_modules_page": "Пользовательские модули — страница {page}/{count}",
            "found_modules": "Найдены модули",
            "no_exact_match": "Точного совпадения нет",
            "module_not_found": "Модуль не найден",
            "no_description": "Нет описания",
            "no_commands": "Нет команд",
            "and_more": "и ещё {count}",
            "and_more_commands": "и ещё {count} команд",
            "aliases": "алиасы",
            "author": "Автор",
            "version": "Версия",
            "description": "Описание",
            "command": "Команды",
            "placeholders_title": "Плейсхолдеры конфигурации",
            "close": "Закрыть",
            "closed": "Закрыто",
            "page_error": "Ошибка страницы",
            "search_hint": "Используйте .man <имя> для поиска",
            "error": "Ошибка",
            "system_module_note": "Системный модуль защищён и не может быть выгружен обычными средствами.",
            "module_hidden": "Модуль скрыт из списка",
            "module_unhidden": "Модуль снова отображается",
            "module_already_hidden": "Модуль уже скрыт",
            "module_not_hidden": "Модуль не скрыт",
            "manhide_usage": "Использование: .manhide <имя>",
            "manunhide_usage": "Использование: .manunhide <имя>",
            "settings_title": "Настройки Tek",
            "settings_usage": "Использование: .tekset <ключ> <значение>",
            "settings_saved": "Настройка <code>{}</code> сохранена: <code>{}</code>",
            "settings_bad_key": "Неизвестная настройка: <code>{}</code>",
            "settings_error": "Не удалось изменить настройку: {}",
            "translator_native": "native",
            "translator_mcub": "mcub_compat_beta",
            "translator_hikka": "hikka_compat",
            "module_type_class": "native: class-style module",
            "module_type_kernel": "native: kernel-style module",
            "module_type_client_old": "native: legacy client-style module",
            "module_type_method": "native: method-style module",
            "module_type_hikka": "hikka_compat",
            "module_type_hikka_library": "hikka_compat library",
            "module_config_info": "Конфигурация: {count} параметров",
            "kernel_not_full_loaded": "Ядро загружено не полностью: {status}",
            "usage": "Использование: .man [имя | номер страницы]",
        },
        "uk": {
            "system_modules": "Системні модулі",
            "user_modules_page": "Користувацькі модулі — сторінка {page}/{count}",
            "found_modules": "Знайдені модулі",
            "no_exact_match": "Точного збігу немає",
            "module_not_found": "Модуль не знайдено",
            "no_description": "Немає опису",
            "no_commands": "Немає команд",
            "and_more": "та ще {count}",
            "and_more_commands": "та ще {count} команд",
            "aliases": "аліаси",
            "author": "Автор",
            "version": "Версія",
            "description": "Опис",
            "command": "Команди",
            "placeholders_title": "Плейсхолдери конфігурації",
            "close": "Закрити",
            "closed": "Закрито",
            "page_error": "Помилка сторінки",
            "search_hint": "Використовуйте .man <ім'я> для пошуку",
            "error": "Помилка",
            "system_module_note": "Системний модуль захищений.",
            "module_hidden": "Модуль приховано зі списку",
            "module_unhidden": "Модуль знову відображається",
            "module_already_hidden": "Модуль уже приховано",
            "module_not_hidden": "Модуль не приховано",
            "manhide_usage": "Використання: .manhide <ім'я>",
            "manunhide_usage": "Використання: .manunhide <ім'я>",
            "settings_title": "Налаштування Tek",
            "settings_usage": "Використання: .tekset <ключ> <значення>",
            "settings_saved": "Налаштування <code>{}</code> збережено: <code>{}</code>",
            "settings_bad_key": "Невідоме налаштування: <code>{}</code>",
            "settings_error": "Не вдалося змінити налаштування: {}",
            "translator_native": "native",
            "translator_mcub": "mcub_compat_beta",
            "translator_hikka": "hikka_compat",
            "module_type_class": "native: class-style module",
            "module_type_kernel": "native: kernel-style module",
            "module_type_client_old": "native: legacy client-style module",
            "module_type_method": "native: method-style module",
            "module_type_hikka": "hikka_compat",
            "module_type_hikka_library": "hikka_compat library",
            "module_config_info": "Конфігурація: {count} параметрів",
            "kernel_not_full_loaded": "Ядро завантажено не повністю: {status}",
            "usage": "Використання: .man [ім'я | номер сторінки]",
        },
        "en": {
            "system_modules": "System modules",
            "user_modules_page": "User modules — page {page}/{count}",
            "found_modules": "Found modules",
            "no_exact_match": "No exact match",
            "module_not_found": "Module not found",
            "no_description": "No description",
            "no_commands": "No commands",
            "and_more": "and {count} more",
            "and_more_commands": "and {count} more commands",
            "aliases": "aliases",
            "author": "Author",
            "version": "Version",
            "description": "Description",
            "command": "Commands",
            "placeholders_title": "Configuration placeholders",
            "close": "Close",
            "closed": "Closed",
            "page_error": "Page error",
            "search_hint": "Use .man <name> to search",
            "error": "Error",
            "system_module_note": "System module is protected.",
            "module_hidden": "Module hidden from the list",
            "module_unhidden": "Module is visible again",
            "module_already_hidden": "Module is already hidden",
            "module_not_hidden": "Module is not hidden",
            "manhide_usage": "Usage: .manhide <name>",
            "manunhide_usage": "Usage: .manunhide <name>",
            "settings_title": "Tek settings",
            "settings_usage": "Usage: .tekset <key> <value>",
            "settings_saved": "Setting <code>{}</code> saved: <code>{}</code>",
            "settings_bad_key": "Unknown setting: <code>{}</code>",
            "settings_error": "Could not change setting: {}",
            "translator_native": "native",
            "translator_mcub": "mcub_compat_beta",
            "translator_hikka": "hikka_compat",
            "module_type_class": "native: class-style module",
            "module_type_kernel": "native: kernel-style module",
            "module_type_client_old": "native: legacy client-style module",
            "module_type_method": "native: method-style module",
            "module_type_hikka": "hikka_compat",
            "module_type_hikka_library": "hikka_compat library",
            "module_config_info": "Configuration: {count} parameters",
            "kernel_not_full_loaded": "Kernel is not fully loaded: {status}",
            "usage": "Usage: .man [name | page number]",
        },
    }

    # Full MCUB Man customization. The inline-bot-only setting/functionality is
    # deliberately omitted; normal userbot messages and media remain supported.
    config = ModuleConfig(
        ConfigValue("man_quote_media", True, description="Send media in quotes", validator=Boolean()),
        ConfigValue("man_banner_url", "", description="Banner image URL", validator=String()),
        ConfigValue("man_invert_media", False, description="Invert media colors", validator=Boolean()),
        ConfigValue("man_emoji_system_list", "▫️", description="Emoji for system modules", validator=String()),
        ConfigValue("man_emoji_user_list", "▪️", description="Emoji for user modules", validator=String()),
        ConfigValue("man_emoji", CUSTOM_EMOJI["crystal"], description="Main Man emoji", validator=String()),
        ConfigValue("man_emoji_no_command", "❔", description="Emoji for modules without commands", validator=String()),
        ConfigValue("man_modules_per_page", MAN_MODULES_PER_PAGE_DEFAULT, description="Modules per page", validator=Integer(min=MAN_MODULES_PER_PAGE_MIN, max=MAN_MODULES_PER_PAGE_MAX)),
        ConfigValue("man_emoji_author", CUSTOM_EMOJI["alembic"], description="Emoji for author/module info", validator=String()),
        ConfigValue("man_emoji_error", CUSTOM_EMOJI["blocked"], description="Emoji for errors", validator=String()),
    )

    @staticmethod
    def _is_webpage_url_invalid_error(error: BaseException) -> bool:
        if not isinstance(error, BadRequestError):
            return False
        return "WEBPAGE_URL_INVALID" in str(getattr(error, "message", "") or error)

    @staticmethod
    def _normalize_http_url(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        url = value.strip()
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""
        return url

    async def _edit_with_banner_retry(self, event: events.NewMessage.Event, text: str, **kwargs: Any) -> Any:
        try:
            return await self.edit(event, text, **kwargs)
        except BadRequestError as e:
            if not self._is_webpage_url_invalid_error(e):
                raise
            fallback = dict(kwargs)
            fallback.pop("file", None)
            fallback.pop("invert_media", None)
            return await self.edit(event, text, **fallback)

    @staticmethod
    def _coerce_modules_per_page(value: Any) -> int:
        if isinstance(value, bool):
            return MAN_MODULES_PER_PAGE_DEFAULT
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return MAN_MODULES_PER_PAGE_DEFAULT
        return max(MAN_MODULES_PER_PAGE_MIN, min(MAN_MODULES_PER_PAGE_MAX, parsed))

    @staticmethod
    def _parse_persisted_config(raw: Any) -> tuple[dict[str, Any], bool]:
        if raw in (None, ""):
            return {}, False
        if isinstance(raw, dict):
            return dict(raw), True
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", errors="replace")
        text = str(raw).strip()
        if not text:
            return {}, False
        try:
            parsed = json.loads(text)
            needs_save = False
        except Exception:
            try:
                parsed = ast.literal_eval(text)
                needs_save = True
            except Exception:
                return {}, True
        return (dict(parsed), needs_save) if isinstance(parsed, dict) else ({}, True)

    async def _repair_persisted_config(self) -> None:
        db_get = getattr(self.kernel, "db_get", None)
        db_set = getattr(self.kernel, "db_set", None)
        if not callable(db_get) or not callable(db_set):
            return
        try:
            raw = await db_get("module_configs", self.name)
        except Exception:
            return
        data, needs_save = self._parse_persisted_config(raw)
        current = data.get("man_modules_per_page", MAN_MODULES_PER_PAGE_DEFAULT)
        coerced = self._coerce_modules_per_page(current)
        if current != coerced:
            data["man_modules_per_page"] = coerced
            needs_save = True
        if needs_save:
            with contextlib.suppress(Exception):
                await db_set("module_configs", self.name, json.dumps(data, ensure_ascii=False, indent=2))

    def _repair_live_config(self) -> None:
        cfg = getattr(self, "config", None)
        if cfg is None or not hasattr(cfg, "get"):
            return
        current = cfg.get("man_modules_per_page", MAN_MODULES_PER_PAGE_DEFAULT)
        coerced = self._coerce_modules_per_page(current)
        if current != coerced:
            with contextlib.suppress(Exception):
                cfg["man_modules_per_page"] = coerced

    async def on_load(self) -> None:
        await self._repair_persisted_config()
        try:
            await super().on_load()
        except Exception as e:
            self.log.warning("Recovered from invalid Tek config during on_load: %s", e)
        self._repair_live_config()
        with contextlib.suppress(Exception):
            self.kernel.store_module_config_schema(self.name, self.config)

    def _type_module_strings(self):
        return self.strings("type_module") if "type_module" in self.strings else self.strings

    def _find_hikka_library(self, name: str, module: Any | None = None) -> Any | None:
        wanted = str(name).lower()
        libraries = getattr(self.kernel, "_hikka_compat_libraries", []) or []
        if not isinstance(libraries, (list, tuple, set)):
            return None
        for library in libraries:
            class_name = library.__class__.__name__
            names = {str(getattr(library, "name", "") or "").lower(), class_name.lower()}
            if class_name.endswith("Lib"):
                names.add(class_name[:-3].lower())
            if module is library or wanted in names:
                return library
        return None

    def _detect_native_module_style(self, name: str, module: Any, target: Any) -> str:
        if target is not module or isinstance(target, ModuleBase):
            return self._s("module_type_class")
        loader = getattr(self.kernel, "_loader", None)
        module_name = getattr(module, "__name__", name)
        cache = getattr(loader, "_module_type_cache", {}) or {}
        cached_type = cache.get(module_name) or cache.get(name)
        if cached_type in {"class", "new", "old", "method"}:
            return {
                "class": self._s("module_type_class"),
                "new": self._s("module_type_kernel"),
                "old": self._s("module_type_client_old"),
                "method": self._s("module_type_method"),
            }[cached_type]
        register = getattr(module, "register", None)
        if callable(register):
            iter_methods = getattr(loader, "_iter_register_methods", None)
            with contextlib.suppress(Exception):
                if callable(iter_methods) and iter_methods(register):
                    return self._s("module_type_kernel")
            with contextlib.suppress(TypeError, ValueError):
                params = list(inspect.signature(register).parameters.values())
                if params:
                    return self._s("module_type_kernel" if params[0].name == "kernel" else "module_type_client_old")
        return self._s("module_type_kernel")

    def _build_module_type_text(self, name: str, typ: str, module: Any, *, hikka_compat: bool = False, hikka_library: bool = False) -> str:
        from ..core.lib.module_runtime import translator_message
        source = ""
        with contextlib.suppress(Exception):
            source = inspect.getsource(getattr(module, "_class_instance", None) or module)
        return translator_message(module, source, hikka=hikka_compat, library=(hikka_library or typ == "library" or self._find_hikka_library(name, module)))

    @staticmethod
    def _count_module_config_keys(config: Any) -> int:
        if config is None:
            return 0
        for attr in ("_values", "_config"):
            values = getattr(config, attr, None)
            if isinstance(values, dict):
                return len(values)
        schema = getattr(config, "schema", None)
        if isinstance(schema, list):
            return len(schema)
        if isinstance(config, dict):
            return len([k for k in config if k != "__mcub_config__"])
        keys = getattr(config, "keys", None)
        if callable(keys):
            with contextlib.suppress(Exception):
                return len([k for k in keys() if k != "__mcub_config__"])
        return 0

    def _module_config_key_count(self, name: str, module: Any | None = None) -> int:
        live = getattr(self.kernel, "_live_module_configs", {}) or {}
        candidates = [live.get(name)]
        target = getattr(module, "_class_instance", None) or module
        if target is not None:
            target_name = getattr(target, "name", None)
            candidates += [getattr(target, "config", None), live.get(target_name) if target_name else None]
        for config in candidates:
            count = self._count_module_config_keys(config)
            if count:
                return count
        return 0

    def _build_module_config_text(self, name: str, module: Any | None = None) -> str:
        count = self._module_config_key_count(name, module)
        return self._s("module_config_info", count=count) if count else ""

    def _module_path(self, name: str, typ: str) -> str:
        if typ == "system":
            return f"{self.kernel.MODULES_DIR}/{name}.py"
        resolved = self.kernel._loader.get_module_path(name)
        if resolved:
            return resolved
        package_dir = f"{self.kernel.MODULES_LOADED_DIR}/{name}"
        init_file = os.path.join(package_dir, "__init__.py")
        return init_file if os.path.exists(init_file) else f"{self.kernel.MODULES_LOADED_DIR}/{name}.py"

    async def _load_module_metadata(self, name: str, typ: str) -> dict:
        fallback = {"commands": {}, "description": self._s("no_description"), "description_i18n": {}, "version": "?.?.?", "author": "unknown", "banner_url": None}
        module_obj = (getattr(self.kernel, "system_modules", {}) if typ == "system" else getattr(self.kernel, "loaded_modules", {})).get(name)
        if typ == "library":
            module_obj = self._find_hikka_library(name)
        target = getattr(module_obj, "_class_instance", None) or module_obj
        if target is not None:
            runtime_version = getattr(target, "version", None)
            if isinstance(runtime_version, str) and runtime_version.strip():
                fallback["version"] = runtime_version.strip()
            runtime_author = getattr(target, "author", None)
            if isinstance(runtime_author, str) and runtime_author.strip():
                fallback["author"] = runtime_author.strip()
            runtime_desc = getattr(target, "description", None)
            if isinstance(runtime_desc, dict):
                fallback["description_i18n"] = runtime_desc
                fallback["description"] = self.kernel._loader.pick_localized_text(runtime_desc, self._lang(), self._s("no_description"))
            elif isinstance(runtime_desc, str) and runtime_desc.strip():
                fallback["description"] = runtime_desc.strip()
        if typ == "library":
            return fallback
        path = self._module_path(name, typ)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return fallback
        lock = _get_metadata_lock()
        async with lock:
            cached = _METADATA_CACHE.get(path)
            if cached and cached[0] == mtime:
                return cached[1]
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                metadata = await self.kernel.get_module_metadata(f.read())
        except Exception:
            metadata = fallback
        if not isinstance(metadata, dict):
            metadata = fallback
        for key in ("commands", "description", "description_i18n", "version", "author", "banner_url"):
            metadata.setdefault(key, fallback.get(key))
        async with lock:
            _METADATA_CACHE[path] = (mtime, metadata)
        return metadata

    def _commands(self, name: str) -> tuple[dict, dict, dict]:
        try:
            return self.kernel._loader.get_module_commands(name, self._lang())
        except Exception:
            return {}, {}, {}

    def _lang(self) -> str:
        return self.kernel.config.get("language", "ru") or "ru"

    def _s(self, key: str, **kwargs: Any) -> str:
        try:
            value = self.strings(key)
        except Exception:
            value = key
        return value.format(**kwargs) if kwargs else value

    async def _get_hidden_modules(self) -> list[str]:
        try:
            data = await self.kernel.db_get("man", "hidden_modules")
        except Exception:
            return []
        if not data:
            return []
        try:
            return json.loads(data) if isinstance(data, str) else json.loads(str(data))
        except Exception:
            return []

    async def _save_hidden_modules(self, hidden: list[str]) -> None:
        await self.kernel.db_set("man", "hidden_modules", json.dumps(hidden, ensure_ascii=False))

    def _gather_all_modules(self, show_hidden: bool, hidden: list[str]) -> dict[str, tuple[str, object]]:
        all_modules: dict[str, tuple[str, object]] = {}
        for name, module in getattr(self.kernel, "system_modules", {}).items():
            all_modules[str(name)] = ("system", module)
        for name, module in getattr(self.kernel, "loaded_modules", {}).items():
            all_modules[str(name)] = ("user", module)
        libs = getattr(self.kernel, "_hikka_compat_libraries", []) or []
        if isinstance(libs, (list, tuple, set)):
            for library in libs:
                library_name = getattr(library, "name", None) or library.__class__.__name__
                all_modules[str(library_name)] = ("library", library)
        if not show_hidden:
            all_modules = {k: v for k, v in all_modules.items() if k not in hidden}
        return all_modules

    def _format_module_line(self, name: str, typ: str, module: Any, hidden: list[str], show_hidden: bool = False) -> str:
        target = getattr(module, "_class_instance", None) or module
        display_name = getattr(type(target), "name", name) if getattr(module, "_class_instance", None) else name
        emoji = self.config.get("man_emoji_system_list", "▫️") if typ == "system" else self.config.get("man_emoji_user_list", "▪️")
        commands, aliases, _ = self._commands(name)
        hidden_mark = f" {CUSTOM_EMOJI['eye_off']}" if show_hidden and name in hidden else ""
        cmd_parts = []
        for cmd in list(commands)[:3]:
            line = f"<code>{self.kernel.custom_prefix}{cmd}</code>"
            alias_data = aliases.get(cmd) if isinstance(aliases, dict) else None
            if alias_data:
                if isinstance(alias_data, str):
                    alias_data = [alias_data]
                line += " [" + ", ".join(f"<code>{self.kernel.custom_prefix}{a}</code>" for a in list(alias_data)[:2]) + "]"
            cmd_parts.append(line)
        if len(commands) > 3:
            cmd_parts.append(f"(+{len(commands)-3})")
        if not cmd_parts:
            cmd_text = f"{self.config.get('man_emoji_no_command') or CUSTOM_EMOJI['snowflake']} {self._s('no_commands')}"
        else:
            cmd_text = ", ".join(cmd_parts)
        # Translator information is intentionally hidden from the module list.
        # It is shown only on `.tek <module>` detail pages.
        return f"{emoji} <code>{html.escape(str(display_name))}</code>{hidden_mark}: {cmd_text}\n"

    def _translator(self, module: Any) -> tuple[str, str]:
        target = getattr(module, "_class_instance", None) or module
        if getattr(target, "_hikka_compat", False) or getattr(target, "_module_type", "") in {"hikka", "geek"}:
            return "🔵", self._s("translator_hikka")
        path = getattr(module, "__file__", None) or getattr(target, "__file__", None)
        source = ""
        if path:
            with contextlib.suppress(Exception):
                source = Path(path).read_text(encoding="utf-8", errors="ignore")
        markers = ("from .. import loader", "from .. import loader, utils", "from .. import utils, loader", "@loader.tds", "loader.Module")
        if any(marker in source for marker in markers):
            return "🟠", self._s("translator_mcub")
        return "🟢", self._s("translator_native")

    async def _build_module_detail(self, name: str, typ: str, module: Any) -> tuple[str, str | None]:
        s = self._s
        target = getattr(module, "_class_instance", None) or module
        display_name = getattr(type(target), "name", name) if getattr(module, "_class_instance", None) else name
        commands, aliases_info, descriptions = self._commands(name)
        metadata = await self._load_module_metadata(name, typ)
        lang = self._lang()
        i18n = metadata.get("description_i18n")
        fallback = metadata.get("description", s("no_description"))
        description = self.kernel._loader.pick_localized_text(i18n, lang, fallback)

        msg = f"<blockquote>{self.config.get('man_emoji') or CUSTOM_EMOJI['dna']} <b>{html.escape(str(display_name))}</b> <i>(v{html.escape(str(metadata.get('version', '1.0.0')))}</i>)</blockquote>\n"
        msg += f"<blockquote expandable>{self.config.get('man_emoji_author') or CUSTOM_EMOJI['alembic']} <i>{html.escape(str(description))}</i></blockquote>\n"
        module_type = self._build_module_type_text(name, typ, module)
        if module_type:
            msg += f"<blockquote>{CUSTOM_EMOJI['tot']} <i>{html.escape(module_type)}</i></blockquote>\n"
        config_text = self._build_module_config_text(name, module)
        if config_text:
            msg += f"<blockquote>{CUSTOM_EMOJI['tot']} <i>{html.escape(config_text)}</i></blockquote>\n"
        msg += "\n<blockquote expandable>"
        if commands:
            lines = []
            for cmd in commands:
                cmd_desc = descriptions.get(cmd) or metadata.get("commands", {}).get(cmd) or f"{CUSTOM_EMOJI['confused']} {s('no_description')}"
                line = f"{self.config.get('man_emoji_system_list' if typ == 'system' else 'man_emoji_user_list', CUSTOM_EMOJI['tot'])} <code>{self.kernel.custom_prefix}{html.escape(str(cmd))}</code> - <b>{html.escape(str(cmd_desc))}</b>"
                if isinstance(aliases_info, dict) and aliases_info.get(cmd):
                    aliases = aliases_info[cmd]
                    if isinstance(aliases, str):
                        aliases = [aliases]
                    line += f" | {s('aliases')}: " + ", ".join(f"<code>{self.kernel.custom_prefix}{html.escape(str(a))}</code>" for a in aliases)
                lines.append(line)
            msg += "\n".join(lines) + "\n"
        else:
            msg += f"{self.config.get('man_emoji_no_command') or CUSTOM_EMOJI['snowflake']} {s('no_commands')}\n"
        msg += "</blockquote>"
        author = metadata.get("author", "unknown")
        msg += f"<blockquote>{self.config.get('man_emoji_author') or CUSTOM_EMOJI['alembic']} <b>{s('author')}:</b> <i>{html.escape(str(author))}</i></blockquote>"
        placeholder_docs = utils.config_placeholders(name)
        if placeholder_docs:
            msg += f"\n<blockquote expandable>{CUSTOM_EMOJI['map']} <b>{s('placeholders_title')}:</b>\n<i>{html.escape(placeholder_docs)}</i></blockquote>"
        if typ == "system":
            msg += "\n<blockquote>" + self._s("system_module_note") + "</blockquote>"
        return msg, self._normalize_http_url(metadata.get("banner_url"))

    async def _show(self, event: events.NewMessage.Event, text: str, banner_url: str = "") -> None:
        configured = self._normalize_http_url(self.config.get("man_banner_url") or "")
        banner = configured or banner_url
        if banner and self.config.get("man_quote_media", False):
            try:
                await self._edit_with_banner_retry(event, text, file=InputMediaWebPage(banner, optional=True), parse_mode="html", invert_media=self.config.get("man_invert_media", False))
                return
            except Exception:
                pass
        if banner and not self.config.get("man_quote_media", False):
            with contextlib.suppress(Exception):
                await self._edit_with_banner_retry(event, text, file=banner, parse_mode="html", invert_media=self.config.get("man_invert_media", False))
                return
        await self.edit(event, text, parse_mode="html")

    def _page_text(self, page: int, hidden: list[str], show_hidden: bool = False) -> str:
        all_modules = self._gather_all_modules(show_hidden, hidden)
        system = sorted((n, v) for n, v in all_modules.items() if v[0] == "system")
        user = sorted((n, v) for n, v in all_modules.items() if v[0] != "system")
        per_page = self._coerce_modules_per_page(self.config.get("man_modules_per_page", 10))
        chunks = [user[i:i+per_page] for i in range(0, len(user), per_page)] or [[]]
        page = max(0, min(page, len(chunks)-1))
        msg = f"{self.config.get('man_emoji') or CUSTOM_EMOJI['crystal']} <b>{self._s('system_modules')}:</b> <code>{len(system)}</code> | <code>{len(user)}</code>"
        if system:
            msg += "<blockquote expandable>" + "".join(self._format_module_line(n, t, m, hidden, show_hidden) for n, (t, m) in system) + "</blockquote>"
        current = chunks[page]
        if current:
            msg += f"<blockquote expandable>{''.join(self._format_module_line(n, t, m, hidden, show_hidden) for n, (t, m) in current)}</blockquote>"
        if len(chunks) > 1:
            msg += f"\n<i>{self._s('user_modules_page', page=page+1, count=len(chunks))}</i>"
            msg += f"\n<code>.man -p {page+1}</code>"
        status = getattr(self.kernel, "load_kernel", None)
        if status and status != "full":
            msg += f"\n<blockquote>{self._s('kernel_not_full_loaded', status=status)}</blockquote>"
        return msg

    async def _generate_detailed_page(self, search_term: str, show_hidden: bool = False) -> tuple[str, str | None]:
        hidden = await self._get_hidden_modules()
        all_modules = self._gather_all_modules(show_hidden, hidden)
        term = search_term.casefold()
        exact = next(((n, t, m) for n, (t, m) in all_modules.items() if n.casefold() == term), None)
        if exact:
            return await self._build_module_detail(*exact)
        similar = []
        for name, (typ, module) in all_modules.items():
            if term in name.casefold():
                similar.append((name, typ, module))
                continue
            commands, _, _ = self._commands(name)
            if any(term in str(cmd).casefold() for cmd in commands):
                similar.append((name, typ, module))
        if len(similar) == 1:
            return await self._build_module_detail(*similar[0])
        if similar:
            msg = f"{self.config.get('man_emoji') or CUSTOM_EMOJI['crystal']} <b>{self._s('found_modules')}:</b>\n<blockquote expandable>"
            for name, typ, module in similar[:20]:
                msg += self._format_module_line(name, typ, module, hidden, show_hidden)
            msg += "</blockquote>\n<blockquote><i>" + self._s("no_exact_match") + f"</i> {CUSTOM_EMOJI['map']}</blockquote>"
            return msg, None
        return f"<blockquote>{self.config.get('man_emoji_error') or CUSTOM_EMOJI['blocked']} {self._s('module_not_found')}</blockquote>", None

    @command("man", alias=["tek", "help"], doc_ru="<имя> список модулей или информация о модуле", doc_en="<name> module list or module information")
    async def cmd_man(self, event: events.NewMessage.Event) -> None:
        try:
            raw = self.args_raw(event).strip()
            if not raw:
                hidden = await self._get_hidden_modules()
                await self._show(event, self._page_text(0, hidden))
                return
            args = raw.split()
            show_hidden = "-f" in args
            args = [a for a in args if a != "-f"]
            if not args:
                hidden = await self._get_hidden_modules()
                await self._show(event, self._page_text(0, hidden, show_hidden))
                return
            if len(args) == 2 and args[0] in {"-p", "--page"} and args[1].isdigit():
                hidden = await self._get_hidden_modules()
                await self._show(event, self._page_text(max(0, int(args[1])-1), hidden, show_hidden))
                return
            search_term = " ".join(args)
            msg, banner = await self._generate_detailed_page(search_term, show_hidden=show_hidden)
            await self._show(event, msg, banner)
        except Exception as e:
            self.log.error("Tek command error: %s\n%s", e, traceback.format_exc())
            await self.edit(event, f"{self.config.get('man_emoji_error') or CUSTOM_EMOJI['blocked']} {self._s('error')}: <code>{html.escape(str(e)[:200])}</code>", parse_mode="html")

    @command("manhide", doc_ru="<имя> скрыть модуль из списка man", doc_en="<name> hide a module from man")
    async def cmd_manhide(self, event: events.NewMessage.Event) -> None:
        name = self.args_raw(event).strip()
        if not name:
            await self.edit(event, self._s("manhide_usage"), parse_mode="html")
            return
        all_names = set(getattr(self.kernel, "system_modules", {})) | set(getattr(self.kernel, "loaded_modules", {}))
        if name not in all_names:
            matches = [n for n in all_names if name.casefold() in n.casefold()]
            if len(matches) != 1:
                await self.edit(event, f"{self.config.get('man_emoji_error') or CUSTOM_EMOJI['blocked']} {self._s('module_not_found')}", parse_mode="html")
                return
            name = matches[0]
        hidden = await self._get_hidden_modules()
        if name in hidden:
            await self.edit(event, self._s("module_already_hidden"), parse_mode="html")
            return
        hidden.append(name)
        await self._save_hidden_modules(hidden)
        await self.edit(event, f"{self._s('module_hidden')}\n<code>{html.escape(name)}</code>", parse_mode="html")

    @command("manunhide", doc_ru="<имя> показать модуль в списке man", doc_en="<name> show a module in man")
    async def cmd_manunhide(self, event: events.NewMessage.Event) -> None:
        name = self.args_raw(event).strip()
        if not name:
            await self.edit(event, self._s("manunhide_usage"), parse_mode="html")
            return
        hidden = await self._get_hidden_modules()
        if name not in hidden:
            matches = [n for n in hidden if name.casefold() in n.casefold()]
            if len(matches) != 1:
                await self.edit(event, self._s("module_not_hidden"), parse_mode="html")
                return
            name = matches[0]
        hidden.remove(name)
        await self._save_hidden_modules(hidden)
        await self.edit(event, f"{self._s('module_unhidden')}\n<code>{html.escape(name)}</code>", parse_mode="html")

    @command("tekcfg", doc_ru="показать все настройки Tek", doc_en="show all Tek settings")
    async def cmd_tekcfg(self, event: events.NewMessage.Event) -> None:
        lines = [f"{self.config.get('man_emoji') or CUSTOM_EMOJI['crystal']} <b>{self._s('settings_title')}</b>"]
        for key in ("man_quote_media", "man_banner_url", "man_invert_media", "man_emoji_system_list", "man_emoji_user_list", "man_emoji", "man_emoji_no_command", "man_modules_per_page", "man_emoji_author", "man_emoji_error"):
            value = self.config.get(key)
            if key == "man_banner_url" and value:
                value = html.escape(str(value))
            else:
                value = html.escape(str(value))
            lines.append(f"<code>{key}</code> = <code>{value}</code>")
        await self.edit(event, "\n".join(lines), parse_mode="html")

    @command("tekset", doc_ru="изменить настройку Tek: .tekset ключ значение", doc_en="change a Tek setting: .tekset key value")
    async def cmd_tekset(self, event: events.NewMessage.Event) -> None:
        raw = self.args_raw(event).strip()
        if not raw:
            await self.edit(event, self._s("settings_usage"), parse_mode="html")
            return
        parts = raw.split(maxsplit=1)
        key = parts[0]
        if key not in self.config:
            await self.edit(event, self._s("settings_bad_key", key), parse_mode="html")
            return
        if len(parts) == 1:
            await self.edit(event, f"<code>{key}</code> = <code>{html.escape(str(self.config.get(key)))}</code>", parse_mode="html")
            return
        value = parts[1]
        try:
            current = self.config.get(key)
            if isinstance(current, bool):
                value = value.lower() in {"1", "true", "yes", "on", "да"}
            elif isinstance(current, int) and not isinstance(current, bool):
                value = int(value)
            self.config[key] = value
            with contextlib.suppress(Exception):
                await self.kernel.db_set("module_configs", self.name, json.dumps(dict(self.config), ensure_ascii=False, default=str))
            await self.edit(event, self._s("settings_saved").format(key, html.escape(str(value))), parse_mode="html")
        except Exception as e:
            await self.edit(event, self._s("settings_error", html.escape(str(e))), parse_mode="html")
