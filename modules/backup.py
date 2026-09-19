"""Backup — резервные копии юзербота.

Сохраняет критичные данные: config.json, data/, modules_custom/ и
(опционально) сессию. Упаковывает в tar.gz и отправляет владельцу
в Telegram или оставляет локально.

Сессия — это полный доступ к аккаунту, поэтому по умолчанию она
в бэкап НЕ входит. Включай только если понимаешь риски.

Команды:
  .backup         — создать и отправить бэкап
  .backup local   — создать локально (не отправлять в Telegram)
  .backup list    — список бэкапов
  .backups N      — периодичность в часах, 0 = выкл авто-бэкапы
"""
from __future__ import annotations
import io
import logging
import os
import tarfile
import time
from pathlib import Path
from core.tetko import Module, command, loop, db_get, db_set
log = logging.getLogger('TETKO.module.backup')
BACKUP_DIR = Path('data/backups')
MAX_LOCAL_BACKUPS = 5
INCLUDE_PATHS = ['config.json', 'data/tetko_db', 'data/tetko_config', 'modules_custom']
SESSION_FILES = ['tetko.session', 'tetko.session-journal']

class Backup(Module):
    name = 'Backup'
    __compat__ = '0.0.9.0'
    version = '1.0.0'
    author = '@FBurgerx'
    description = 'Резервные копии config, data и модулей'
    config = {'auto_interval_hours': 0, 'include_session': False, 'notify': True}

    def _make_backup(self, include_session: bool=False) -> Path | None:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        out_path = BACKUP_DIR / f'tetko_backup_{stamp}.tar.gz'
        paths = [p for p in INCLUDE_PATHS if Path(p).exists()]
        if include_session:
            paths += [p for p in SESSION_FILES if Path(p).exists()]
        if not paths:
            log.warning('backup: нечего бэкапить')
            return None
        try:
            with tarfile.open(out_path, 'w:gz') as tar:
                for p in paths:
                    tar.add(p)
        except Exception as e:
            log.error(f'backup: не удалось создать архив: {e}')
            return None
        self._rotate_local()
        return out_path

    def _rotate_local(self) -> None:
        """Оставить только последние MAX_LOCAL_BACKUPS архивов."""
        try:
            backups = sorted(BACKUP_DIR.glob('tetko_backup_*.tar.gz'), key=lambda p: p.stat().st_mtime)
            for old in backups[:-MAX_LOCAL_BACKUPS]:
                old.unlink()
        except Exception as e:
            log.debug(f'backup rotate failed: {e}')

    def _list_local(self) -> list[Path]:
        if not BACKUP_DIR.exists():
            return []
        return sorted(BACKUP_DIR.glob('tetko_backup_*.tar.gz'), key=lambda p: p.stat().st_mtime)

    @command(name='backup', doc='Создать резервную копию', only_for='owner')
    async def cmd_backup(self, event, args):
        action = args[0].strip().lower() if args else 'send'
        if action == 'list':
            backups = self._list_local()
            if not backups:
                await self.respond(event, '📂 <b>Бэкапы</b>\n\nПусто.', parse_mode='html')
                return
            lines = []
            for b in backups:
                size_kb = round(b.stat().st_size / 1024, 1)
                lines.append(f'▫️ <code>{b.name}</code> ({size_kb} KB)')
            await self.respond(event, '📂 <b>Локальные бэкапы</b>\n\n' + '\n'.join(lines), parse_mode='html')
            return
        include_session = bool(self.cfg.get('include_session', False))
        if args and 'session' in ' '.join(args).lower():
            include_session = True
        await self.respond(event, '🗃 Создаю архив...')
        out_path = self._make_backup(include_session=include_session)
        if out_path is None:
            await self.respond(event, '❌ Не удалось создать бэкап.')
            return
        size_kb = round(out_path.stat().st_size / 1024, 1)
        note = ''
        if include_session:
            note = '\n\n⚠ <b>В архиве сессия — полный доступ к аккаунту!</b>'
        if action == 'local':
            await self.respond(event, f'✅ <b>Бэкап создан</b>\n\n▫️ <code>{out_path}</code>\n▫️ Размер: <code>{size_kb} KB</code>{note}', parse_mode='html')
            return
        try:
            await event.delete()
        except Exception:
            pass
        try:
            await self.client.send_file(event.chat_id, file=str(out_path), caption=f'🗃 <b>Бэкап TETKO</b>\n▫️ Файл: <code>{out_path.name}</code>\n▫️ Размер: <code>{size_kb} KB</code>{note}', parse_mode='html')
        except Exception as e:
            log.error(f'backup: отправка не удалась: {e}')
            await self.respond(event, f'⚠ Не удалось отправить архив, но он сохранён локально:\n<code>{out_path}</code>', parse_mode='html')

    @loop(interval=3600)
    async def auto_backup_loop(self):
        hours = int(self.cfg.get('auto_interval_hours', 0) or 0)
        if hours <= 0:
            return
        last = db_get('backup', 'last_auto', 0)
        now = time.time()
        if now - last < hours * 3600:
            return
        out_path = self._make_backup(include_session=bool(self.cfg.get('include_session', False)))
        db_set('backup', 'last_auto', now)
        if out_path is None:
            return
        if not self.cfg.get('notify', True):
            return
        admin_id = None
        if self.kernel and self.kernel.context:
            admin_id = self.kernel.context.admin_id
        if not admin_id:
            return
        size_kb = round(out_path.stat().st_size / 1024, 1)
        try:
            await self.client.send_file(admin_id, file=str(out_path), caption=f'🗃 <b>Авто-бэкап TETKO</b>\n▫️ <code>{out_path.name}</code> ({size_kb} KB)', parse_mode='html')
        except Exception as e:
            log.error(f'backup: авто-отправка не удалась: {e}')