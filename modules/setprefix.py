"""SetPrefix — смена префикса команд на лету.

Префикс хранится в трёх местах ядра: kernel.prefix, kernel.context.prefix
и kernel.dispatcher.prefix. Все три обновляются синхронно, иначе диспетчер
продолжит слушать старый префикс, а пользователь — новый. Значение также
пишется в config.json, чтобы перезапуск ничего не сбросил.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from core.tetko import Module, command
log = logging.getLogger('TETKO.module.setprefix')
CONFIG_PATH = Path('config.json')
MAX_PREFIX_LEN = 8

def _esc(text: str) -> str:
    """Экранирование HTML (префикс попадает в HTML-сообщение)."""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

class SetPrefix(Module):
    name = 'SetPrefix'
    __compat__ = '0.0.9.0'
    version = '1.0.0'
    author = '@FBurgerx'
    description = 'Смена префикса команд на лету (.setprefix <новый>)'

    @command(name='setprefix', aliases=['prefix', 'sp'], doc='Изменить префикс команд', only_for='owner')
    async def cmd_setprefix(self, event, args):
        kernel = self.kernel
        if kernel is None:
            await self.respond(event, '❌ Ядро недоступно.')
            return
        current = kernel.prefix
        if not args:
            await self.respond(event, f'🔧 <b>Префикс команд</b>\n\nТекущий: <code>{_esc(current)}</code>\n\n<i>Использование:</i> <code>{_esc(current)}setprefix &lt;новый&gt;</code>\n<i>Например:</i> <code>{_esc(current)}setprefix !</code>', parse_mode='html')
            return
        new = ' '.join(args).strip()
        if not new:
            await self.respond(event, '❌ Префикс не может быть пустым.')
            return
        if len(new) > MAX_PREFIX_LEN:
            await self.respond(event, f'❌ Слишком длинный префикс (максимум {MAX_PREFIX_LEN} символов).')
            return
        if new == current:
            await self.respond(event, f'🤷 Префикс и так <code>{_esc(current)}</code>.')
            return
        kernel.prefix = new
        kernel.config['command_prefix'] = new
        if kernel.context is not None:
            kernel.context.prefix = new
        if kernel.dispatcher is not None:
            kernel.dispatcher.prefix = new
        saved = True
        try:
            CONFIG_PATH.write_text(json.dumps(kernel.config, ensure_ascii=False, indent=4), encoding='utf-8')
        except Exception as e:
            saved = False
            log.error(f'setprefix: не удалось записать config.json: {e}')
        status = '💾 Сохранено в <code>config.json</code>' if saved else '⚠ Не удалось сохранить в config.json (работает до перезапуска)'
        await self.respond(event, f'✅ <b>Префикс изменён</b>\n\n<code>{_esc(current)}</code> → <code>{_esc(new)}</code>\n\n{status}\n\n<i>Теперь команды:</i> <code>{_esc(new)}ping</code>, <code>{_esc(new)}tek</code>', parse_mode='html')