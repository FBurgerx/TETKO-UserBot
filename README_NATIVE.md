# Native core

The native runtime is independent from MCUB and Hikka compatibility layers.
Modules are registered through `NativeRegistry`, executed by `NativeDispatcher`,
and managed by `NativeLifecycle`.

## Telegram запуск

```bash
pip install -r requirements.txt
export TETKO_API_ID=123456
export TETKO_API_HASH=your_api_hash
export TETKO_SESSION=tetko
python run_tetko.py
```
При первом запуске Telethon попросит номер телефона, код Telegram и пароль 2FA, если он включён.
