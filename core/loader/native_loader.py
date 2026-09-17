"""Safe-ish loader for TETKO native modules + MCUB compat."""
import ast
import importlib.util
import inspect
import hashlib
import sys
from pathlib import Path

from core.native.module import NativeModule


class NativeLoadError(RuntimeError):
    pass


class NativeLoadResult:
    def __init__(self, module, source_path, digest, translator="native"):
        self.module = module
        self.source_path = str(source_path)
        self.sha256 = digest
        self.translator = translator


# ═══════════════════════════════════════════════════════════════
#   MCUB-совместимый слой
# ═══════════════════════════════════════════════════════════════
def _get_module_base():
    """Ленивый импорт ModuleBase (может не быть, если нет mcub-слоя)."""
    try:
        from core.lib.loader.base import ModuleBase
        return ModuleBase
    except ImportError:
        return None


class MCUBAdapter:
    """
    Обёртка над MCUB-модулем (наследником ModuleBase),
    чтобы он вёл себя как native-модуль в ядре.
    """

    def __init__(self, instance, import_name: str):
        self._instance = instance
        self._import_name = import_name
        self._mcub_compat_release = True  # маркер для translatorchecker

    # ---- Прокси к реальному модулю ----
    def __getattr__(self, item):
        return getattr(self._instance, item)

    # ---- Поля, которые ждёт ядро ----
    @property
    def name(self):
        return getattr(self._instance, "name", self._instance.__class__.__name__)

    @property
    def module_name(self):
        return self.name

    @property
    def version(self):
        return getattr(self._instance, "version", "0.0.0")

    @property
    def author(self):
        return getattr(self._instance, "author", "unknown")

    @property
    def description(self):
        return getattr(self._instance, "description", "")

    # ---- Lifecycle ----
    async def on_load(self):
        # ModuleBase может иметь свой on_load
        hook = getattr(self._instance, "on_load", None)
        if hook is None:
            return
        result = hook()
        if inspect.isawaitable(result):
            await result

    async def on_unload(self):
        hook = getattr(self._instance, "on_unload", None)
        if hook is None:
            return
        result = hook()
        if inspect.isawaitable(result):
            await result

    # ---- Регистрация handler'ов ----
    def collect_handlers(self):
        """
        Собрать handler'ы, которые декораторы MCUB записали
        в _cmd_registry / _watcher_registry / и т.д.
        Возвращает список HandlerSpec-like объектов.
        """
        specs = []

        # Все реестры из ModuleBase
        registry_map = {
            "_cmd_registry": "command",
            "_watcher_registry": "watcher",
            "_callback_registry": "callback",
            "_inline_registry": "inline",
            "_loop_registry": "loop",
            "_event_registry": "event",
            "_method_registry": "method",
            "_bot_cmd_registry": "bot_command",
            "_owner_registry": "owner_only",
            "_permission_registry": "permission",
            "_error_handler_registry": "error_handler",
            "_inline_temp_registry": "inline_temp",
        }

        for attr_name, kind in registry_map.items():
            registry = getattr(self._instance, attr_name, None)
            if not registry:
                continue
            for entry in registry:
                specs.append((kind, entry, self._instance))

        return specs

    def __repr__(self):
        return f"<MCUBAdapter {self.name} v{self.version}>"


# ═══════════════════════════════════════════════════════════════
#   Основной loader
# ═══════════════════════════════════════════════════════════════
class NativeLoader:
    def __init__(self, registry, context=None):
        self.registry = registry
        self.context = context
        self.loaded = {}

    # ---------- ВАЛИДАЦИЯ ----------
    def validate_source(self, source, filename="<module>"):
        try:
            ast.parse(source, filename=filename)
        except SyntaxError as e:
            raise NativeLoadError(f"syntax error: {e}") from e

    # ---------- ПОИСК КЛАССОВ ----------
    def _classes_native(self, namespace):
        """Наследники NativeModule."""
        return [
            v for v in namespace.values()
            if inspect.isclass(v)
            and issubclass(v, NativeModule)
            and v is not NativeModule
        ]

    def _classes_mcub(self, namespace):
        """Наследники ModuleBase (MCUB-стиль)."""
        ModuleBase = _get_module_base()
        if ModuleBase is None:
            return []
        return [
            v for v in namespace.values()
            if inspect.isclass(v)
            and issubclass(v, ModuleBase)
            and v is not ModuleBase
        ]

    # ---------- ЗАГРУЗКА ----------
    async def load_file(self, path):
        path = Path(path)
        source = path.read_text(encoding="utf-8")
        self.validate_source(source, str(path))

        digest = hashlib.sha256(source.encode()).hexdigest()
        name = f"tetko_native_{digest[:16]}"

        spec = importlib.util.spec_from_file_location(name, path)
        if not spec or not spec.loader:
            raise NativeLoadError("cannot create import spec")

        module_obj = importlib.util.module_from_spec(spec)
        sys.modules[name] = module_obj

        try:
            spec.loader.exec_module(module_obj)

            native_classes = self._classes_native(vars(module_obj))
            mcub_classes = self._classes_mcub(vars(module_obj))

            if native_classes:
                return await self._load_native_classes(
                    native_classes, path, digest, name
                )

            if mcub_classes:
                return await self._load_mcub_classes(
                    mcub_classes, path, digest, name
                )

            raise NativeLoadError(
                "no NativeModule or ModuleBase subclass found"
            )

        except Exception:
            sys.modules.pop(name, None)
            raise

    async def _load_native_classes(self, classes, path, digest, import_name):
        """Загрузить native-классы (текущая логика)."""
        results = []
        for cls in classes:
            instance = cls(self.context)
            if hasattr(self.registry, "register"):
                self.registry.register(instance)
            if inspect.iscoroutinefunction(instance.on_load):
                await instance.on_load()
            else:
                instance.on_load()
            self.loaded[instance.module_name] = (instance, import_name)
            results.append(NativeLoadResult(instance, path, digest, "native"))
        return results

    async def _load_mcub_classes(self, classes, path, digest, import_name):
        """Загрузить MCUB-классы через адаптер."""
        results = []
        for cls in classes:
            try:
                instance = cls()
            except TypeError:
                # Некоторые ModuleBase-модули могут требовать kernel/context
                try:
                    instance = cls(self.context)
                except Exception as e:
                    raise NativeLoadError(
                        f"cannot instantiate {cls.__name__}: {e}"
                    ) from e

            adapter = MCUBAdapter(instance, import_name)

            # Регистрируем адаптер в registry
            if hasattr(self.registry, "register"):
                self.registry.register(adapter)

            # Собираем handler'ы и регистрируем их
            self._register_mcub_handlers(adapter)

            # on_load
            await adapter.on_load()

            self.loaded[adapter.module_name] = (adapter, import_name)
            results.append(NativeLoadResult(adapter, path, digest, "mcub_compat"))

        return results

    def _register_mcub_handlers(self, adapter):
        """Регистрирует handler'ы MCUB-модуля в нашем registry."""
        specs = adapter.collect_handlers()
        if not specs:
            return

        # Пробуем использовать наш HandlerSpec, если он есть
        try:
            from core.native.handlers import HandlerSpec
        except ImportError:
            HandlerSpec = None

        for kind, entry, module in specs:
            # entry — это либо tuple, либо объект с .name/.callback
            cmd_name = None
            cmd_callback = None
            aliases = []

            if isinstance(entry, tuple):
                # Формат: (callback, name, aliases)
                cmd_callback = entry[0]
                if len(entry) > 1:
                    cmd_name = entry[1]
                if len(entry) > 2 and isinstance(entry[2], (list, tuple)):
                    aliases = list(entry[2])
            else:
                cmd_name = getattr(entry, "name", None)
                cmd_callback = getattr(entry, "callback", entry)

            if not cmd_name:
                cmd_name = getattr(cmd_callback, "__name__", "unknown")

            # Пытаемся зарегистрировать через наш registry
            reg = self.registry
            if hasattr(reg, "register_handler") and HandlerSpec is not None:
                try:
                    spec = HandlerSpec(
                        name=cmd_name,
                        callback=cmd_callback,
                        kind=kind if kind in ("command", "watcher", "callback") else "command",
                        aliases=aliases,
                        owner=module,
                    )
                    reg.register_handler(spec)
                except Exception as e:
                    print(f"[TETKO] cannot register {kind} {cmd_name}: {e}")

    # ---------- ВЫГРУЗКА ----------
    async def unload(self, module_name):
        item = self.loaded.pop(module_name, None)
        if not item:
            return False
        instance, import_name = item
        try:
            result = instance.on_unload()
            if inspect.isawaitable(result):
                await result
        finally:
            if hasattr(self.registry, "unregister"):
                self.registry.unregister(module_name)
            sys.modules.pop(import_name, None)
        return True
