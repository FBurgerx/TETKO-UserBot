"""Trusted — управление доверенными пользователями.

Доверенные могут выполнять команды с only_for="trusted" и нажимать
inline-кнопки. Список хранится в data/tetko_db/trusted.json.

Команды:
  .trust <id/@username>   — добавить
  .untrust <id/@username> — убрать
  .trusted                — список
"""
from __future__ import annotations
import logging
from core.tetko import Module, command, db_get, db_set
log = logging.getLogger('TETKO.module.trusted')
NS = 'trusted'

class Trusted(Module):
    name = 'Trusted'
    __compat__ = '0.0.9.0'
    version = '1.0.0'
    author = '@FBurgerx'
    description = 'Управление доверенными пользователями'

    def _load(self) -> list[int]:
        data = db_get(NS, 'users', [])
        return [int(u) for u in data if isinstance(u, int) or str(u).isdigit()]

    def _save(self, users: list[int]) -> None:
        db_set(NS, 'users', sorted(set(users)))

    def _push_to_context(self) -> None:
        """Синхронизируем кэш контекста — его читает диспетчер."""
        if self.kernel and self.kernel.context is not None:
            self.kernel.context.trusted = set(self._load())

    async def _resolve(self, arg: str) -> int | None:
        """Превратить аргумент в user_id: число или @username."""
        arg = arg.strip().lstrip('@')
        if arg.isdigit():
            return int(arg)
        try:
            ent = await self.client.get_entity(arg)
            uid = getattr(ent, 'id', None)
            return int(uid) if uid else None
        except Exception as e:
            log.warning(f'trust: не удалось найти {arg!r}: {e}')
            return None

    async def on_load(self) -> None:
        self._push_to_context()

    @command(name='trust', doc='Сделать пользователя доверенным', only_for='owner')
    async def cmd_trust(self, event, args):
        if not args:
            await self.respond(event, '❌ Укажите ID или @username.\nИспользование: <code>.trust @user</code>', parse_mode='html')
            return
        uid = await self._resolve(args[0])
        if uid is None:
            await self.respond(event, f'❌ Не удалось найти пользователя <code>{args[0]}</code>', parse_mode='html')
            return
        users = self._load()
        if uid in users:
            await self.respond(event, f'🤷 Пользователь <code>{uid}</code> уже доверенный.', parse_mode='html')
            return
        users.append(uid)
        self._save(users)
        self._push_to_context()
        await self.respond(event, f'✅ <code>{uid}</code> теперь доверенный.', parse_mode='html')

    @command(name='untrust', doc='Убрать пользователя из доверенных', only_for='owner')
    async def cmd_untrust(self, event, args):
        if not args:
            await self.respond(event, '❌ Укажите ID или @username.\nИспользование: <code>.untrust @user</code>', parse_mode='html')
            return
        uid = await self._resolve(args[0])
        if uid is None:
            await self.respond(event, f'❌ Не удалось найти пользователя <code>{args[0]}</code>', parse_mode='html')
            return
        users = self._load()
        if uid not in users:
            await self.respond(event, f'🤷 Пользователь <code>{uid}</code> и так не доверенный.', parse_mode='html')
            return
        users.remove(uid)
        self._save(users)
        self._push_to_context()
        await self.respond(event, f'🗑 Пользователь <code>{uid}</code> больше не доверенный.', parse_mode='html')

    @command(name='trusted', aliases=['trustlist'], doc='Список доверенных', only_for='owner')
    async def cmd_trusted(self, event, args):
        users = self._load()
        owner = getattr(self.kernel.context, 'admin_id', None) if self.kernel else None
        if not users:
            await self.respond(event, '👥 <b>Доверённые</b>\n\nСписок пуст.\n\n<i>Добавить:</i> <code>.trust @user</code>', parse_mode='html')
            return
        lines = [f'▫️ <code>{u}</code>' for u in users]
        await self.respond(event, f'👥 <b>Доверённые</b> ({len(users)})\n\n' + '\n'.join(lines) + f'\n\n<i>Владелец:</i> <code>{owner}</code>', parse_mode='html')