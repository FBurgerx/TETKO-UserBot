"""HotReload — применяет изменения модулей на лету.

Слежу за modules/ и modules_custom/ через @loop. Как только .py-файл
меняется (ты отредактировал его в редакторе, DLM скачал обновление,
rsync синхронизировал папку) — модуль выгружается и загружается заново
с новым кодом. Перезапуск не нужен.

Команды:
  .hotreload       — вкл/выкл
  .hotreload now   — применить все изменения немедленно
  .hotreload check — проверить, что изменилось, не применяя
"""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Any
from core.tetko import Module, command, loop, db_get, db_set
log = logging.getLogger('TETKO.module.hotreload')
MODULES_DIR = Path('modules')
CUSTOM_DIR = Path('modules_custom')
DEBOUNCE_SECONDS = 2.0

class HotReload(Module):
    name = 'HotReload'
    __compat__ = '0.0.9.0'
    version = '1.0.0'
    author = '@FBurgerx'
    description = 'Применяет изменения модулей на лету, без перезапуска'
    config = {'enabled': True, 'check_interval': 3, 'notify': True}

    def _load_state(self) -> dict[str, float]:
        """{путь: mtime} — последнее известное время изменения каждого файла."""
        data = db_get('hotreload', 'mtimes', {})
        return {str(k): float(v) for k, v in data.items()} if data else {}

    def _save_state(self, state: dict[str, float]) -> None:
        db_set('hotreload', 'mtimes', state)

    def _scan(self) -> dict[str, float]:
        """Собрать mtime всех .py-файлов в обоих модульных папках."""
        result: dict[str, float] = {}
        for base in (MODULES_DIR, CUSTOM_DIR):
            if not base.exists():
                continue
            for path in base.glob('*.py'):
                if path.name.startswith('_') or path.name == '__init__.py':
                    continue
                try:
                    result[str(path)] = path.stat().st_mtime
                except OSError:
                    pass
        return result

    async def on_load(self) -> None:
        if self.cfg.get('enabled', True):
            state = self._scan()
            self._save_state(state)

    def _diff(self) -> list[tuple[str, str]]:
        """Вернуть [(путь, 'changed'|'new'|'removed')] для изменившихся файлов."""
        now = self._scan()
        before = self._load_state()
        changes: list[tuple[str, str]] = []
        for path, mtime in now.items():
            old = before.get(path)
            if old is None:
                changes.append((path, 'new'))
            elif mtime > old:
                changes.append((path, 'changed'))
        for path in before:
            if path not in now:
                changes.append((path, 'removed'))
        return changes

    async def _apply(self, path_str: str, kind: str) -> bool:
        """Перезагрузить один модуль. Возвращает True при успехе."""
        loader = getattr(self.client, 'loader', None)
        if loader is None:
            return False
        path = Path(path_str)
        file_stem = path.stem
        reg_name = None
        for name, mod in loader.registry._modules.items():
            spec = loader._spec_names.get(name, '')
            if spec.endswith(f'.{file_stem}'):
                reg_name = name
                break
        if kind == 'removed':
            if reg_name:
                try:
                    await loader.unload_module(reg_name)
                    return True
                except Exception as e:
                    log.error(f'hotreload: unload {file_stem} failed: {e}')
            return False
        if reg_name:
            try:
                await loader.unload_module(reg_name)
            except Exception as e:
                log.warning(f'hotreload: выгрузка {file_stem} не удалась: {e}')
        try:
            await loader.load_module_from_file(path)
            return True
        except Exception as e:
            log.error(f'hotreload: загрузка {path} не удалась: {e}')
            return False

    @loop(interval=3)
    async def watch_loop(self):
        if not self.cfg.get('enabled', True):
            return
        try:
            changes = self._diff()
        except Exception as e:
            log.debug(f'hotreload scan failed: {e}')
            return
        if not changes:
            return
        await asyncio.sleep(DEBOUNCE_SECONDS)
        applied = []
        for path, kind in self._diff():
            ok = await self._apply(path, kind)
            if ok:
                applied.append((path, kind))
        self._save_state(self._scan())
        if applied and self.cfg.get('notify', True):
            names = [Path(p).stem for p, _ in applied]
            try:
                admin_id = self.kernel.context.admin_id if self.kernel else None
                if admin_id:
                    await self.client.send_message(admin_id, '♻️ <b>HotReload</b>\n\n' + '\n'.join((f'• <code>{Path(p).stem}</code> — {k}' for p, k in applied)) + f'\n\n<i>Применено модулей: {len(names)}</i>', parse_mode='html')
            except Exception as e:
                log.debug(f'hotreload notify failed: {e}')

    @command(name='hotreload', aliases=['hr'], doc='Применять изменения модулей на лету', only_for='owner')
    async def cmd_hotreload(self, event, args):
        if not args:
            enabled = not self.cfg.get('enabled', True)
            self.cfg.set('enabled', enabled)
            if enabled:
                self._save_state(self._scan())
            await self.respond(event, f"♻️ <b>HotReload</b>\n\nСостояние: <code>{('включён' if enabled else 'выключен')}</code>", parse_mode='html')
            return
        action = args[0].strip().lower()
        if action == 'now':
            changes = self._diff()
            if not changes:
                await self.respond(event, '✅ Изменений нет.')
                return
            applied = []
            for path, kind in changes:
                if await self._apply(path, kind):
                    applied.append((path, kind))
            self._save_state(self._scan())
            await self.respond(event, '♻️ <b>HotReload</b> — применено\n\n' + '\n'.join((f'• <code>{Path(p).stem}</code> — {k}' for p, k in applied)) or 'ничего не изменилось', parse_mode='html')
            return
        if action == 'check':
            changes = self._diff()
            if not changes:
                await self.respond(event, '✅ Изменений нет.')
                return
            await self.respond(event, '🔍 <b>HotReload</b> — найдено изменений\n\n' + '\n'.join((f'• <code>{Path(p).stem}</code> — {k}' for p, k in changes)), parse_mode='html')
            return
        await self.respond(event, '❌ Неизвестное действие.\nИспользование: <code>.hotreload</code> | <code>.hotreload now</code> | <code>.hotreload check</code>', parse_mode='html')