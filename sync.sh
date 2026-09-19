#!/usr/bin/env bash
# Синхронизация: ~/TETKO-UserBot (git-репо для фиксов) → ~/tetko-live (рабочая папка)
#
# Копирует только код и конфиги. НЕ трогает:
#   config.json, *.session, data/, modules_custom/, logs/
# то есть всё, что содержит твои данные и авторизацию.
#
# Использование: bash ~/tetko-live/sync.sh
set -euo pipefail

SRC="$HOME/TETKO-UserBot"
DST="$HOME/tetko-live"

if [ ! -d "$SRC/.git" ]; then
    echo "❌ $SRC — не git-репо. Проверь путь."
    exit 1
fi

echo "🔄 Синхронизация $SRC → $DST"
echo "   (код и конфиги копируются, твои данные не трогаются)"
echo

# Что НЕ копируется ни при каких условиях
SKIP=(
    --exclude '.git'
    --exclude 'config.json'
    --exclude '*.session'
    --exclude '*.session-journal'
    --exclude 'data'
    --exclude 'modules_custom'
    --exclude 'logs'
    --exclude '__pycache__'
    --exclude '*.pyc'
    --exclude '*.bak'
)

# Сначала выводим, что изменилось
echo "── Изменения ──"
rsync -rLltD --delete "${SKIP[@]}" --dry-run --itemize-changes "$SRC/" "$DST/" \
    | grep -v '^\.' || true
echo

# Прогон
rsync -rLltD --delete "${SKIP[@]}" "$SRC/" "$DST/"

echo
echo "✅ Готово. Код в $DST обновлён."
echo
echo "Не скопировано (осталось от рабочей установки):"
echo "  config.json, *.session, data/, modules_custom/"
