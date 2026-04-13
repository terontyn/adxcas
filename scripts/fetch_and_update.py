"""
fetch_and_update.py  (Bot API версия)
--------------------------------------
Читает сообщения из Telegram-канала через Bot API,
фильтрует по ключевому слову и (если доступно) имени автора,
парсит цены, сохраняет в telegram_prices.json.

GitHub Secrets:
  TG_BOT_TOKEN    — токен бота от @BotFather
  TG_SENDER_NAME  — имя отправителя (Юлия). Необязательно если
                    канал не подписывает посты — тогда берём
                    последнее сообщение с ценами.
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from parse_tg_prices import parse_message

# ──────────────────────────────────────────────
BOT_TOKEN    = os.environ["TG_BOT_TOKEN"]
SENDER_NAME  = os.environ.get("TG_SENDER_NAME", "").strip().lower()
OUTPUT_JSON  = Path(__file__).parent.parent / "telegram_prices.json"
PRICE_KEYWORD = "руб"
# ──────────────────────────────────────────────


def tg_request(method: str, params: dict = None) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def get_updates(offset: int | None = None) -> list:
    params = {"limit": 100, "timeout": 0, "allowed_updates": '["channel_post"]'}
    if offset is not None:
        params["offset"] = offset
    result = tg_request("getUpdates", params)
    if not result.get("ok"):
        print(f"Ошибка getUpdates: {result}")
        return []
    return result.get("result", [])


def sender_matches(post: dict) -> bool:
    """
    Проверяет автора поста.
    Если SENDER_NAME не задан — пропускаем проверку (True).
    Если канал не подписывает посты (нет author_signature) — тоже True,
    т.к. фильтровать нечего.
    """
    if not SENDER_NAME:
        return True

    signature = post.get("author_signature", "").strip().lower()
    fwd = post.get("forward_from") or {}
    fwd_name = (
        (fwd.get("first_name") or "") + " " + (fwd.get("last_name") or "")
    ).strip().lower()

    # Если подписи нет вообще — канал не подписывает посты,
    # фильтр по автору невозможен → принимаем все ценовые сообщения
    if not signature and not fwd_name:
        return True

    return SENDER_NAME in signature or SENDER_NAME in fwd_name


def is_price_message(text: str) -> bool:
    """Проверяет что сообщение содержит цены топлива."""
    t = text.lower()
    return PRICE_KEYWORD in t and any(
        kw in t for kw in ["тн", "тонн", "руб/тн", "руб./тн"]
    )


def load_existing(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"history": [], "last_update_id": None}


def save_json(data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Сохранено: {path}")


def main():
    data = load_existing(OUTPUT_JSON)

    last_id = data.get("last_update_id")
    offset  = (last_id + 1) if last_id else None

    print(f"Последний обработанный update_id: {last_id}")
    updates = get_updates(offset)
    print(f"Получено обновлений: {len(updates)}")

    # Диагностика: печатаем что видим в первых обновлениях
    has_signatures = False
    for upd in updates[:5]:
        post = upd.get("channel_post", {})
        sig  = post.get("author_signature", "")
        txt  = (post.get("text") or "")[:60]
        if sig:
            has_signatures = True
        print(f"  update_id={upd['update_id']} | sig={sig!r:15} | text={txt!r}")

    if updates and not has_signatures:
        print("ℹ️  Канал не подписывает посты — фильтр по автору отключён, "
              "берём последнее ценовое сообщение")

    found_text  = None
    new_last_id = last_id

    for update in updates:
        update_id = update["update_id"]
        new_last_id = max(new_last_id or 0, update_id)

        post = update.get("channel_post", {})
        text = post.get("text", "")

        if not text:
            print(f"  [{update_id}] Нет текста — пропуск")
            continue

        # Фильтр по ключевым словам цен
        if not is_price_message(text):
            print(f"  [{update_id}] Не ценовое сообщение — пропуск")
            continue

        # Фильтр по автору
        if not sender_matches(post):
            sig = post.get("author_signature", "—")
            print(f"  [{update_id}] Автор {sig!r} — не совпадает, пропуск")
            continue

        sig = post.get("author_signature", "канал")
        print(f"  [{update_id}] ✅ Ценовое сообщение от {sig!r}: {text[:80]}…")
        found_text = text  # берём последнее подходящее

    # Сохраняем offset в любом случае
    if new_last_id:
        data["last_update_id"] = new_last_id

    if not found_text:
        print("Новых ценовых сообщений не найдено.")
        save_json(data, OUTPUT_JSON)
        sys.exit(0)

    parsed    = parse_message(found_text)
    today_str = parsed["date"]

    existing_dates = [entry["date"] for entry in data.get("history", [])]
    if today_str in existing_dates:
        print(f"Цены на {today_str} уже актуальны.")
        save_json(data, OUTPUT_JSON)
        sys.exit(0)

    data.setdefault("history", []).insert(0, parsed)
    data["history"] = data["history"][:30]
    data["latest"]     = parsed
    data["updated_at"] = datetime.utcnow().isoformat() + "Z"

    save_json(data, OUTPUT_JSON)
    print(f"✅ Цены на {today_str} обновлены. Позиций: {len(parsed['prices'])}")


if __name__ == "__main__":
    main()
