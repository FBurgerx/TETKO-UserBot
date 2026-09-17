# SPDX-License-Identifier: MIT
# Copyright (c) 2026 flexownerAL, @anhedonuya
"""Debug module — показывает список команд и модулей."""
from core.lib.loader.module_base import ModuleBase, command


class Debug(ModuleBase):
    name = "debug"
    version = "1.0.0"
    author = "@anhedonuya"
    description = {"ru": "Отладка", "en": "Debug"}

    @command("dbgcommands", doc={"ru": "список команд", "en": "list commands"})
    async def cmd_dbgcommands(self, event):
        cmds = sorted(getattr(self.kernel, "command_handlers", {}).keys())
        owners = getattr(self.kernel, "command_owners", {})
        lines = [f"<b>Всего команд:</b> <code>{len(cmds)}</code>\n"]
        for c in cmds:
            owner = owners.get(c, "?")
            lines.append(f"• <code>.{c}</code> — {owner}")
        text = "\n".join(lines) if cmds else "Нет команд"
        await event.edit(text)

    @command("dbgmodules", doc={"ru": "модули", "en": "modules"})
    async def cmd_dbgmodules(self, event):
        mods = getattr(self.kernel, "loaded_modules", {})
        lines = [f"<b>Модулей:</b> <code>{len(mods)}</code>\n"]
        for name in sorted(mods.keys()):
            lines.append(f"• <code>{name}</code>")
        text = "\n".join(lines) if mods else "Нет модулей"
        await event.edit(text)

    @command("dbginfo", doc={"ru": "инфо ядра", "en": "kernel info"})
    async def cmd_dbginfo(self, event):
        k = self.kernel
        info = [
            f"<b>Kernel:</b> <code>{type(k).__name__}</code>",
            f"<b>command_handlers:</b> <code>{len(getattr(k, 'command_handlers', {}))}</code>",
            f"<b>loaded_modules:</b> <code>{len(getattr(k, 'loaded_modules', {}))}</code>",
            f"<b>aliases:</b> <code>{len(getattr(k, 'aliases', {}))}</code>",
            f"<b>prefix:</b> <code>{getattr(k, 'custom_prefix', '?')}</code>",
            f"<b>my id:</b> <code>{getattr(k, 'ADMIN_ID', '?')}</code>",
        ]
        await event.edit("\n".join(info))
