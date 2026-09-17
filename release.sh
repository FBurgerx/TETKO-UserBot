#!/data/data/com.termux/files/usr/bin/bash
# ─────────────────────────────────────────────────────────
# TETKO Auto-Release Script
# Bump version → commit → push → tag
# Copyright (c) 2026 flexownerAL, @anhedonuya
# ─────────────────────────────────────────────────────────

set -e

cd "$(dirname "$0")"

echo "═══════════════════════════════════════"
echo "  TETKO Auto-Release"
echo "═══════════════════════════════════════"
echo ""

# ─── 1. Bump version ───
echo "[1/5] Bump version..."
python3 << 'PYEOF'
from pathlib import Path
import re

def bump_version(v: str) -> str:
    parts = [int(x) for x in v.split(".")]
    while len(parts) < 4:
        parts.append(0)
    parts[3] += 1
    for i in range(3, 0, -1):
        if parts[i] >= 20:
            parts[i] = 0
            parts[i - 1] += 1
    return ".".join(str(p) for p in parts)

p = Path("core/version.py")
src = p.read_text(encoding="utf-8")
match = re.search(r'__version__\s*=\s*"([\d.]+)"', src)
if not match:
    print("  ❌ Не нашёл __version__")
    exit(1)

old_ver = match.group(1)
new_ver = bump_version(old_ver)

src = re.sub(r'__version__\s*=\s*"[\d.]+"', f'__version__ = "{new_ver}"', src)
p.write_text(src, encoding="utf-8")

# Сохраняем для следующих шагов
Path(".release_version").write_text(new_ver, encoding="utf-8")
print(f"  {old_ver} → {new_ver}")
PYEOF

VERSION=$(cat .release_version)
echo "  Новая версия: $VERSION"
echo ""

# ─── 2. Обновляем VERSION.md ───
echo "[2/5] Обновляем VERSION.md..."
python3 << PYEOF
from pathlib import Path
import datetime

p = Path("VERSION.md")
if not p.exists():
    p.write_text("# TETKO Version History\n\n", encoding="utf-8")

src = p.read_text(encoding="utf-8")
date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

header = "# TETKO Version History\n\n"
entry = f"## $VERSION ({date})\n- Auto-release\n\n"

if header in src:
    src = src.replace(header, header + entry, 1)
else:
    src = header + entry + src

p.write_text(src, encoding="utf-8")
print("  ✅ VERSION.md обновлён")
PYEOF

# ─── 3. Git add + commit ───
echo ""
echo "[3/5] Git commit..."
git add -A

# Проверяем, есть ли что коммитить
if git diff --cached --quiet; then
    echo "  ⚠️ Нечего коммитить"
else
    git commit -m "release: v$VERSION"
    echo "  ✅ Закоммичено"
fi

# ─── 4. Push ───
echo ""
echo "[4/5] Push в GitHub..."
git push origin main
echo "  ✅ Запушено"

# ─── 5. Tag ───
echo ""
echo "[5/5] Создаём тег v$VERSION..."
git tag -a "v$VERSION" -m "TETKO v$VERSION" 2>/dev/null || echo "  ⚠️ Тег уже существует"
git push origin "v$VERSION" 2>/dev/null || echo "  ⚠️ Тег уже запушен"

# ─── Итог ───
echo ""
echo "═══════════════════════════════════════"
echo "  ✅ Release v$VERSION опубликован!"
echo "  🔗 https://github.com/anhedonuya/TETKO-UserBot/releases/tag/v$VERSION"
echo "═══════════════════════════════════════"

# Убираем временный файл
rm -f .release_version
