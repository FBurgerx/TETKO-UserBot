"""Help — список команд и их описания.

У каждой команды в реестре есть поле doc/description, но .tek показывает
только имена модулей. Этот модуль выводит полноценную справку:
  .help              — все команды по модулям
  .help <команда>    — подробности по конкретной команде
"""
from __future__ import annotations
import logging
from typing import Any
from core.tetko import Module, command
log = logging.getLogger('TETKO.module.help')
PAGE_SIZE = 8

class Help(Module):
    name = 'Help'
    __compat__ = '0.0.9.0'
    version = '1.0.0'
    author = '@FBurgerx'
    description = 'Справка по командам юзербота'

    def _doc_of(self, cmd: Any) -> str:
        doc = cmd.doc
        if isinstance(doc, str) and doc.strip():
            return doc.strip()
        if isinstance(doc, dict):
            lang = getattr(self.kernel.context, 'language', 'ru') if self.kernel else 'ru'
            return doc.get(lang) or doc.get('ru') or doc.get('en') or ''
        return ''

    def _access_label(self, cmd: Any) -> str:
        only = cmd.only_for
        if only == 'owner':
            return ' 👑'
        if only == 'trusted':
            return ' 🔓'
        return ''

    @command(name='help', aliases=['h', 'справка'], doc='Список команд и их описания')
    async def cmd_help(self, event, args):
        if self.kernel is None:
            await self.respond(event, '❌ Ядро недоступно.')
            return
        registry = self.kernel.registry
        if args:
            name = args[0].strip().lstrip('.')
            cmd = registry.find_command(name)
            if cmd is None:
                await self.respond(event, f'❌ Команда <code>.{name}</code> не найдена.\n<i>Посмотри список:</i> <code>.help</code>', parse_mode='html')
                return
            doc = self._doc_of(cmd)
            only = cmd.only_for or 'все'
            aliases = ', '.join((f'<code>.{a}</code>' for a in cmd.aliases)) or '—'
            module_name = getattr(cmd.module, 'name', '?')
            text = f'📖 <b>Команда</b> <code>.{cmd.name}</code>\n\n▫️ <b>Модуль:</b> <code>{module_name}</code>\n▫️ <b>Алиасы:</b> {aliases}\n▫️ <b>Доступ:</b> {only}'
            if doc:
                text += f'\n\n💬 <i>{doc}</i>'
            await self.respond(event, text, parse_mode='html')
            return
        commands = registry._commands
        if not commands:
            await self.respond(event, '📭 Команд нет.')
            return
        by_module: dict[str, list[Any]] = {}
        for cmd in commands.values():
            mname = getattr(cmd.module, 'name', '?')
            by_module.setdefault(mname, []).append(cmd)
        total = len(commands)
        lines = [f'📚 <b>Справка TETKO</b> — <code>{total}</code> команд\n']
        for mname in sorted(by_module):
            cmds = sorted(by_module[mname], key=lambda c: c.name)
            lines.append(f'<blockquote><b>{mname}</b>')
            for cmd in cmds:
                doc = self._doc_of(cmd)
                label = f'<code>.{cmd.name}</code>{self._access_label(cmd)}'
                if doc:
                    label += f' — {doc}'
                lines.append(f'  {label}')
            lines.append('</blockquote>')
        text = '\n'.join(lines)
        if len(text) > 4000:
            text = text[:4000] + '\n\n<i>(обрезано)</i>'
        await self.respond(event, text, parse_mode='html')