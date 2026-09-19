# TETKO Version History

## 0.0.9.9 (2026-09-19)

### Новые модули
- **`setprefix`** — смена префикса команд на лету, без перезапуска
- **`help`** — справка по всем командам с описаниями и аргументами
- **`trusted`** — управление доверенными пользователями
- **`hotreload`** — применяет изменения модулей на лету, без перезапуска
- **`backup`** — резервные копии `config.json`, `data/`, `modules_custom/`

### Ядро
- **`protection_mode: "safe"`** — теперь доступен из `config.json`, решает `ScamModuleDetected: GetPasswordRequest blocked`
- **Доверенные пользователи** — `only_for="trusted"` в `@command` и `@callback`.
  Проверка через `context.is_trusted()`, список — `db_get("trusted", "users", [])`
- **FloodWait** теперь ловится в диспетчере: бот засыпает на нужное время, а не падает
- **Supervisor** в `main.py`: авто-реконнект при разрыве связи и защита от падений
- **`terminal`** — команда больше не затирается результатом; выводится ниже

### Поведение
- `.load` скачивает в `modules_custom/` (раньше в `modules/`), DLM теперь может обновлять такие модули
- `.unload` ищет файл в `modules/` и `modules_custom/`
- `.unlm` показывает и отправляет модули из обеих папок
- `main.py` больше не убивает `os.system("clear")` стартовый лог
- Удалены мусорные файлы из репозитория (`logs/`, дубликаты, `png`)

## 0.0.9.8 (2026-09-19)
- fix: _is_system works on Windows paths

## 0.0.9.6 (2026-09-19)
- Inline menus with edit-in-place
- naming: TETKO = kernel, tetko-compat = module style
- DLM: inline + auto-update + edit-in-place
- loader: unlm command
- .gitignore: modules_custom/

## 0.0.9.5 (2026-09-18)
- First working release of tetko-compat kernel
- core/tetko: registry, loader, dispatcher, decorators, kernel, module, config
- main.py reads config.json, session 'tetko'
- Fixed kernel._start_loops, graceful shutdown, precise sys.modules cleanup
- dispatcher: removed pattern_match hack, added handle_callback
- 15 legacy modules moved to modules_legacy/

## 0.0.8.6 (2026-09-17 21:53)
- Auto-release

## 0.0.8.5 (2026-09-17 19:52)
- Auto-release

## 0.0.7.10 (2026-09-17 17:28)
- Auto-release

## 0.0.7.2 (2026-09-17 15:27)
- Auto-release

## 0.0.7.0 (2026-09-17 15:18)
- Auto-release

## 0.0.6.19 (2026-09-17 15:05)
- Auto-release

## 0.0.6.18 (2026-09-17 14:54)
- Auto-release

## 0.0.6.17 (2026-09-17 14:10)
- Auto-release

