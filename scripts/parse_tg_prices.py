"""
parse_tg_prices.py  v2
----------------------
Парсит текст сообщения из Telegram-канала с ценами на топливо.
"""

import re
from datetime import datetime

FUEL_ALIASES = {
    "АИ-92":        "АИ-92",
    "АИ-95":        "АИ-95",
    "АИ-98":        "АИ-98",
    "АИ-100":       "АИ-100",
    "ДТ-Е-К5":      "ДтЕ",
    "ДТЕ К-5":      "ДтЕ",
    "ДТЕ К5":       "ДтЕ",
    "ДТ-Е":         "ДтЕ",
    "ДТЕ":          "ДтЕ",
    "ДТ-З-К5":      "ДтЗ",
    "ДТ-З К5":      "ДтЗ",
    "ДТ-З":         "ДтЗ",
    "ДТ-А-К5":      "ДтА",
    "ДТ-А":         "ДтА",
    "ДТ С":         "ДтЛ",
    "ТС-1":         "ТС-1",
    "РТ":           "РТ",
}

STATION_IDS = {
    "ТАНЕКО":                   "taneko",
    "Нижнекамская НБ":          "nb_nizhnekamsk",
    "Кичуй":                    "kichuy",
    "НПЗ Салават":              "npz_salavat",
    "Кудьма":                   "kudma",
    "НБ Паритет (Йошкар Ола)":  "nb_parity",
    "ЯНОС":                     "yanos",
    "Информат(г. Сургут)":      "informat_surgut",
    "Травники":                 "travniki",
    "ЛПДС Черкассы":            "lpds_cherkassy",
    "ЛПДС Воронеж":             "lpds_voronezh",
    "ЛПДС Никольское":          "lpds_nikolskoe",
    "ЛПДС Невская":             "lpds_nevskaya",
}


def normalize_fuel(raw):
    raw = re.sub(r'\s+', ' ', raw).strip()
    raw = re.sub(r'^\(?ПО ЗАПРОСУ\)?\s*', '', raw, flags=re.I).strip()
    for alias, norm in sorted(FUEL_ALIASES.items(), key=lambda x: -len(x[0])):
        if raw.upper().startswith(alias.upper()):
            return norm
    return raw


def extract_date(text):
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    return m.group(1) if m else datetime.now().strftime("%d.%m.%Y")


def split_price_entries(text, pending_fuel=""):
    entries = []
    parts = re.split(r'руб[./тн]*\.?', text, flags=re.I)
    for i, part in enumerate(parts[:-1]):
        part = part.strip()
        note_in_part = re.search(r'\(([^)]+)\)', part)
        part_clean = re.sub(r'\([^)]*\)', '', part).strip()
        m = re.search(r'^(.*?)\s*[-–—]\s*([\d][\d\s]{3,8})\s*$', part_clean)
        if not m:
            continue
        fuel_raw = m.group(1).strip()
        price_str = re.sub(r'\s', '', m.group(2))
        fuel_raw = re.sub(r'^тн\.?\s*', '', fuel_raw, flags=re.I).strip()
        if not fuel_raw or fuel_raw == '-':
            fuel_raw = pending_fuel
        pending_fuel = ""
        note_next = re.search(r'\(([^)]+)\)', parts[i+1]) if i+1 < len(parts) else None
        note = (note_in_part.group(1) if note_in_part else "") or \
               (note_next.group(1) if note_next else "")
        if price_str.isdigit() and fuel_raw:
            entries.append((fuel_raw, int(price_str), note.strip()))
    return entries


def detect_station(token):
    for name in sorted(STATION_IDS.keys(), key=len, reverse=True):
        if token.startswith(name):
            return name, token[len(name):].strip()
        if name.lower() == token.lower():
            return name, ""
    return None, token


def parse_message(text):
    date = extract_date(text)
    prices = []
    current_station = None
    pending_fuel = ""

    tokens = re.split(r' {2,}|\n', text)
    tokens = [t.strip() for t in tokens if t.strip()]

    for token in tokens:
        if re.match(r'(Доброго|Добрый|Актуальные|Привет)', token, re.I):
            continue

        has_price = 'руб' in token.lower()

        if has_price:
            station_found, remainder = detect_station(token)
            if station_found:
                current_station = station_found
                token = remainder
            entries = split_price_entries(token, pending_fuel)
            pending_fuel = ""
            for fuel_raw, price, note in entries:
                fuel_norm = normalize_fuel(fuel_raw)
                if current_station and fuel_norm:
                    prices.append({
                        "station":    current_station,
                        "station_id": STATION_IDS.get(current_station,
                                        current_station.lower().replace(" ", "_")),
                        "fuel":       fuel_norm,
                        "fuel_raw":   fuel_raw,
                        "price":      price,
                        "note":       note,
                    })
        else:
            station_found, remainder = detect_station(token)
            if station_found:
                current_station = station_found
                pending_fuel = remainder
            else:
                if len(token) < 70 and not re.search(r'\d{5}', token):
                    current_station = token
                    pending_fuel = ""

    return {"date": date, "prices": prices}


if __name__ == "__main__":
    import json
    SAMPLE = (
        "Доброго дня! Актуальные цены на 04.03.2026   ТАНЕКО  АИ-92- 64 400 руб./тн.  "
        "АИ-95- 66 400 руб./тн.  АИ-98 - 94 400 руб./тн  АИ-100 - 96 400 руб./тн  "
        "ДТ-Е-К5 - 60 900 руб./тн ДТ-З-К5 ЕВРО-6 кл2 - 71 000 руб./тн "
        "ДТ-А-К5 ЕВРО-6 - 73 900 руб./тн   ТС-1 - 76 900 руб./тн (ПО ЗАПРОСУ) "
        "РТ- 76 900 руб/тн (ПО ЗАПРОСУ)   Нижнекамская НБ  ДТ-З-К5 ЕВРО-6 кл2 - 71 900 руб./тн   "
        "Кичуй  ДТ-З-К5 кл1 - 67 900 руб./тн   НПЗ Салават АИ-92- 62 500 руб./тн.  "
        "ДТ-З кл2 - 72 200 руб./тн  Кудьма ДТЕ К-5- 61 900 руб./тн  "
        "НБ Паритет (Йошкар Ола) ДТ-Е  - 60 900 руб./тн ДТ-З кл.1 - 68 100 руб./тн  "
        "ЯНОС ДТЕ  - 61 100 руб./тн  Информат(г. Сургут) АИ-92- 61 400 руб./тн.  "
        "АИ-95- 66 400 руб./тн.  ДТ-А - 75 400 руб./тн   Травники ДТ-Е  - 62 900 руб./тн "
        "ДТ-З - 76 900 руб./тн  ЛПДС Черкассы  ДТ С – 61 200 руб.тн.  "
        "ЛПДС Воронеж ДТ С – 61 900 руб.тн.  ЛПДС Никольское  ДТ С – 62 000 руб.тн.  "
        "ЛПДС Невская  ДТ С – 61 500 руб.тн."
    )
    result = parse_message(SAMPLE)
    print(f"Дата: {result['date']}")
    print(f"Всего позиций: {len(result['prices'])}\n")
    for p in result["prices"]:
        note = f"  ⚠ {p['note']}" if p["note"] else ""
        print(f"  {p['station']:30} {p['fuel']:8} {p['price']:>7} ₽/тн{note}")
