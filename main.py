# -*- coding: utf-8 -*-

import os
import glob
import json
import base64
import csv
import datetime
import math
import re
import shutil
from pathlib import Path
from collections import defaultdict
from urllib.request import urlopen, Request
from urllib.error import URLError

import pdfplumber
import pandas as pd
import folium
import requests

# ──────────────────────────────────────────────────────────────────────────────
# НАСТРОЙКИ
# ──────────────────────────────────────────────────────────────────────────────
DATA_FOLDER         = "pdf_data"
STATIONS_CSV        = "stations.csv"
LUKOIL_STATIONS_CSV = "stations_lukoil.csv"   # справочник нефтебаз Лукойл (имя → lat/lon/code)
ROSNEFT_STATIONS_CSV = "rosneft_stations.csv" # отдельный справочник НБ Роснефть
ROSNEFT_PRICES_CSV   = "rosneft_prices.csv"   # отдельный файл цен Роснефть
TRANSIT_CITY_STATIONS_CSV = "transit_city_stations.csv"  # отдельный справочник НБ Транзит Сити
LUKOIL_PRICE_URL    = "https://auto.lukoil.ru/ru/ForBusiness/wholesale/price"
LUKOIL_BASE_URL     = "https://auto.lukoil.ru"
LUKOIL_SPOT_PREFIX  = "lukoil_spot"
PUBLIC_DIR          = "public"

VENDOR_ASSET_URLS = {
    "assets/vendor/leaflet/leaflet.css": "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css",
    "assets/vendor/leaflet/leaflet.js": "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js",
    "assets/vendor/leaflet/images/layers.png": "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/images/layers.png",
    "assets/vendor/leaflet/images/layers-2x.png": "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/images/layers-2x.png",
    "assets/vendor/leaflet/images/marker-icon.png": "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/images/marker-icon.png",
    "assets/vendor/leaflet/images/marker-icon-2x.png": "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/images/marker-icon-2x.png",
    "assets/vendor/leaflet/images/marker-shadow.png": "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/images/marker-shadow.png",
    "assets/vendor/bootstrap/css/bootstrap.min.css": "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css",
    "assets/vendor/bootstrap/js/bootstrap.bundle.min.js": "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js",
    "assets/vendor/jquery/jquery-3.7.1.min.js": "https://code.jquery.com/jquery-3.7.1.min.js",
    "assets/vendor/awesome-markers/leaflet.awesome-markers.css": "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css",
    "assets/vendor/awesome-markers/leaflet.awesome-markers.js": "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js",
    "assets/vendor/awesome-markers/images/markers-soft.png": "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/images/markers-soft.png",
    "assets/vendor/awesome-markers/images/markers-soft@2x.png": "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/images/markers-soft@2x.png",
    "assets/vendor/awesome-markers/images/markers-shadow.png": "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/images/markers-shadow.png",
    "assets/vendor/folium/leaflet.awesome.rotate.min.css": "https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css",
    "assets/vendor/fontawesome/css/all.min.css": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/css/all.min.css",
    "assets/vendor/fontawesome/webfonts/fa-solid-900.woff2": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/webfonts/fa-solid-900.woff2",
    "assets/vendor/fontawesome/webfonts/fa-solid-900.ttf": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/webfonts/fa-solid-900.ttf",
    "assets/vendor/fontawesome/webfonts/fa-regular-400.woff2": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/webfonts/fa-regular-400.woff2",
    "assets/vendor/fontawesome/webfonts/fa-regular-400.ttf": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/webfonts/fa-regular-400.ttf",
    "assets/vendor/fontawesome/webfonts/fa-brands-400.woff2": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/webfonts/fa-brands-400.woff2",
    "assets/vendor/fontawesome/webfonts/fa-brands-400.ttf": "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/webfonts/fa-brands-400.ttf",
    "assets/vendor/bootstrap-glyphicons/css/bootstrap-glyphicons.css": "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css",
    "assets/vendor/bootstrap-glyphicons/fonts/glyphicons-halflings-regular.eot": "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/fonts/glyphicons-halflings-regular.eot",
    "assets/vendor/bootstrap-glyphicons/fonts/glyphicons-halflings-regular.woff": "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/fonts/glyphicons-halflings-regular.woff",
    "assets/vendor/bootstrap-glyphicons/fonts/glyphicons-halflings-regular.ttf": "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/fonts/glyphicons-halflings-regular.ttf",
    "assets/vendor/bootstrap-glyphicons/fonts/glyphicons-halflings-regular.svg": "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/fonts/glyphicons-halflings-regular.svg",
    "assets/vendor/leaflet-routing-machine/leaflet-routing-machine.css": "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css",
    "assets/vendor/leaflet-routing-machine/leaflet-routing-machine.js": "https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js",
    "assets/vendor/oms/oms.min.js": "https://cdn.jsdelivr.net/npm/overlapping-marker-spiderfier-leaflet/dist/oms.min.js",
}

HTML_VENDOR_REWRITES = {
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css": "assets/vendor/leaflet/leaflet.css",
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js": "assets/vendor/leaflet/leaflet.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css": "assets/vendor/bootstrap/css/bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js": "assets/vendor/bootstrap/js/bootstrap.bundle.min.js",
    "https://code.jquery.com/jquery-3.7.1.min.js": "assets/vendor/jquery/jquery-3.7.1.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css": "assets/vendor/awesome-markers/leaflet.awesome-markers.css",
    "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js": "assets/vendor/awesome-markers/leaflet.awesome-markers.js",
    "https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css": "assets/vendor/folium/leaflet.awesome.rotate.min.css",
    "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/css/all.min.css": "assets/vendor/fontawesome/css/all.min.css",
    "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css": "assets/vendor/bootstrap-glyphicons/css/bootstrap-glyphicons.css",
}

TARIFF_PER_KM   = float(os.getenv("TARIFF_PER_KM",   "170"))   # руб/км (рейс)
TRUCK_TONS      = float(os.getenv("TRUCK_TONS",        "25"))   # грузоподъёмность бензовоза, т
OTP_FILE        = "stavkiOTP.txt"

os.makedirs(DATA_FOLDER, exist_ok=True)

# Список ОТП-нефтебаз (ключ совпадает с JS-стороной)
OTP_STATION_KEYS = [
    'лпдс володарская',
    'нс солнечногорская',
    'нс нагорная',
    'лпдс сокур',
    'лпдс невская',
    'лпдс черкассы',
    'лпдс никольское-1',
    'нп брянск',
    'лпдс воронеж',
    'лпдс белгород',
]

def load_otp_prices():
    """Читает stavkiOTP.txt → dict {key: {nalyv, storage}}"""
    prices = {k: {"nalyv": 0, "storage": 0} for k in OTP_STATION_KEYS}
    if not os.path.exists(OTP_FILE):
        return prices
    try:
        with open(OTP_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) >= 3:
                    key     = parts[0].strip().lower()
                    nalyv   = float(parts[1].strip() or 0)
                    storage = float(parts[2].strip() or 0)
                    if key in prices:
                        prices[key] = {"nalyv": nalyv, "storage": storage}
        print(f"✅ Надбавки ОТП загружены из {OTP_FILE}")
    except Exception as e:
        print(f"⚠️  Ошибка чтения {OTP_FILE}: {e}")
    return prices

DEFAULT_TG_STATION_COORDS = {
    "ТАНЕКО":                   (55.605631,  51.961132),
    "Нижнекамская НБ":          (55.638,     51.820),    # Нижнекамск, рядом с ТАНЕКО
    "Кичуй":                    (54.8894,     51.9841),    # пос. Кичуй, Татарстан
    "НПЗ Салават":              (53.3998115, 55.9060868),
    "Салават":                  (53.3998115, 55.9060868),
    "Кудьма":                   (56.1651918, 43.8709444),
    "НБ Паритет (Йошкар Ола)":  (56.631,     47.891),    # Йошкар-Ола
    "ЯНОС":                     (57.5543,    39.8111707),
    "Информат(г. Сургут)":      (61.2835729, 73.2066849),
    "Информат (г.Сургут)":      (61.2835729, 73.2066849),
    "Информат (г. Сургут)":     (61.2835729, 73.2066849),
    "Травники":                 (55.722,     61.578),    # Челябинская обл.
    "ЛПДС Черкассы":            (54.907433,  56.167044),
    "ЛПДС Воронеж":             (51.5157735, 39.4026279),
    "ЛПДС Никольское":          (52.8295156, 40.4080585),
    "ЛПДС Невская":             (59.9005236, 30.741512),
    "НБ Приоритет (Наб. Челны)":  (55.728,     52.404),   # Набережные Челны
    "НБ Приоритет (Набережные Челны)": (55.728, 52.404),
    "ТАИФ-НК":                    (55.595062,  51.907579), # из stations.csv
    "Таиф НК":                    (55.595062,  51.907579),
    "ЛПДС Володарская":           (55.4866265, 37.9730438),# из stations.csv
    "ОРСК":                       (51.254291, 58.512015),
    "ПАО ОРСКНЕФТЕОРГСИНТЕЗ":     (51.254291, 58.512015),
    "ТНАС":                       (55.615670, 49.276375),
    "Татнефтьавиасервис":         (55.615670, 49.276375),
}
 
# Маппинг внутренних ключей топлива → категория карты
TG_FUEL_TO_CAT = {
    "АИ-92":  "Бензин",
    "АИ-95":  "Бензин",
    "АИ-98":  "Бензин",
    "АИ-100": "Бензин",
    "ДтЕ":    "ДтЕ",
    "ДтЗ":    "ДтЗ",
    "ДтА":    "ДтА",
    "ДтЛ":    "ДтЛ",
    "ТС-1":   "ДтЛ",   # авиационный керосин — показываем как летнее ДТ
    "РТ":     "ДтЛ",
}
 
TG_PRICES_JSON = "telegram_prices.json"


def load_transit_city_station_coords(csv_path=TRANSIT_CITY_STATIONS_CSV):
    coords = dict(DEFAULT_TG_STATION_COORDS)
    if not os.path.exists(csv_path):
        return coords
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str).fillna("")
    except Exception as e:
        print(f"⚠️  Ошибка чтения {csv_path}: {e}")
        return coords

    for _, row in df.iterrows():
        lat = parse_coordinates(row.get("lat"))
        lon = parse_coordinates(row.get("lon"))
        if lat is None or lon is None:
            continue
        names = []
        name = str(row.get("name", "")).strip()
        alias = str(row.get("alias", "")).strip()
        if name:
            names.append(name)
        if alias:
            names.extend([x.strip() for x in alias.split("|") if x.strip()])
        for station_name in names:
            coords[station_name] = (lat, lon)
    return coords
 
 
def load_telegram_prices():
    """
    Читает telegram_prices.json и возвращает список маркеров
    в том же формате, что используют spimex/lukoil:
    [{"code", "name", "lat", "lon", "fuels": [{"name", "price", "cat", "date"}]}]
    """
    if not os.path.exists(TG_PRICES_JSON):
        print(f"ℹ️  {TG_PRICES_JSON} не найден — слой Telegram пропущен.")
        return []
 
    try:
        with open(TG_PRICES_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️  Ошибка чтения {TG_PRICES_JSON}: {e}")
        return []
 
    latest = data.get("latest", {})
    tg_station_coords = load_transit_city_station_coords()
    prices = latest.get("prices", [])
    date   = latest.get("date", "")
    # Date for popup in DD.MM.YYYY format
    date_short = date if date else ""
 
    # Группируем по станции
    by_station = defaultdict(list)
    for entry in prices:
        station = entry.get("station", "")
        if station:
            by_station[station].append(entry)
 
    results = []
    unmatched = []
 
    for station, entries in by_station.items():
        coords = tg_station_coords.get(station)
        if coords is None:
            unmatched.append(station)
            continue
 
        lat, lon = coords
        fuels = []
        for e in entries:
            fuel_key = e.get("fuel", "")
            cat = TG_FUEL_TO_CAT.get(fuel_key)
            if cat is None:
                continue
            note = e.get("note", "")
            fuel_display = fuel_key + (f" ({note})" if note else "")
            price_raw = e.get("price")
            try:
                price_value = float(price_raw) if price_raw is not None else None
            except (TypeError, ValueError):
                price_value = None
            fuels.append({
                "name":  fuel_display,
                "price": price_value,
                "cat":   cat,
                "date":  date_short,
            })
 
        if fuels:
            results.append({
                "code":  f"TG_{station.upper().replace(' ', '_')[:12]}",
                "name":  station,
                "lat":   lat,
                "lon":   lon,
                "fuels": fuels,
            })
 
    print(f"✅ Telegram: станций {len(results)}, дата {date}")
    if unmatched:
        print(f"   Не найдены координаты: {', '.join(unmatched)}")
 
    return results


def normalize_station_key(name):
    s = str(name or "").strip().lower().replace("ё", "е")
    return re.sub(r"\s+", " ", s)


def normalize_display_date(value):
    s = str(value or "").strip()
    if not s:
        return ""
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%d.%m.%Y")
        except Exception:
            pass
    m = re.match(r"^(\d{2})\.(\d{2})$", s)
    if m:
        return f"{m.group(1)}.{m.group(2)}.{datetime.datetime.now().year}"
    return s


def load_rosneft_prices(stations_csv=ROSNEFT_STATIONS_CSV, prices_csv=ROSNEFT_PRICES_CSV):
    if not os.path.exists(stations_csv):
        print(f"ℹ️  {stations_csv} не найден — слой Роснефть пропущен.")
        return []
    if not os.path.exists(prices_csv):
        print(f"ℹ️  {prices_csv} не найден — слой Роснефть пропущен.")
        return []

    try:
        stations_df = pd.read_csv(stations_csv, encoding="utf-8-sig", dtype=str).fillna("")
        prices_df = pd.read_csv(prices_csv, encoding="utf-8-sig", dtype=str).fillna("")
    except Exception as e:
        print(f"⚠️  Ошибка чтения CSV Роснефть: {e}")
        return []

    station_map = {}
    for _, row in stations_df.iterrows():
        code = str(row.get("code", "")).strip()
        name = str(row.get("name", "")).strip()
        lat = parse_coordinates(row.get("lat"))
        lon = parse_coordinates(row.get("lon"))
        alias = str(row.get("alias", "")).strip()
        if not code or not name or lat is None or lon is None:
            continue

        station_rec = {"code": code, "name": name, "lat": lat, "lon": lon}
        for key in (name, alias):
            nkey = normalize_station_key(key)
            if nkey and nkey not in station_map:
                station_map[nkey] = station_rec

    grouped = {}
    unmatched = set()
    for _, row in prices_df.iterrows():
        station_name = str(row.get("station", "")).strip()
        fuel_name = str(row.get("fuel", "")).strip()
        price = clean_price(row.get("price"))
        date_short = normalize_display_date(row.get("date", ""))
        if not station_name or not fuel_name or price is None:
            continue

        cat = get_fuel_category(fuel_name)
        if cat is None:
            continue

        station_rec = station_map.get(normalize_station_key(station_name))
        if station_rec is None:
            unmatched.add(station_name)
            continue

        code = station_rec["code"]
        if code not in grouped:
            grouped[code] = {
                "code": code,
                "name": station_rec["name"],
                "lat": station_rec["lat"],
                "lon": station_rec["lon"],
                "fuels": [],
            }

        grouped[code]["fuels"].append({
            "name": fuel_name,
            "price": price,
            "cat": cat,
            "date": date_short,
        })

    results = [v for v in grouped.values() if v.get("fuels")]
    print(f"✅ Роснефть: станций {len(results)}")
    if unmatched:
        print(f"   Не найдены координаты (Роснефть): {', '.join(sorted(unmatched))}")
    return results


def get_rosneft_latest_date(prices_csv=ROSNEFT_PRICES_CSV):
    if not os.path.exists(prices_csv):
        return ""
    try:
        df = pd.read_csv(prices_csv, encoding="utf-8-sig", dtype=str).fillna("")
    except Exception:
        return ""
    if "date" not in df.columns:
        return ""

    parsed = []
    for raw in df["date"].tolist():
        d = normalize_display_date(raw)
        if not d:
            continue
        range_match = re.match(r"^(\d{2}\.\d{2}\.\d{4})-(\d{2}\.\d{2}\.\d{4})$", d)
        if range_match:
            try:
                parsed.append((datetime.datetime.strptime(range_match.group(2), "%d.%m.%Y"), d))
                continue
            except Exception:
                pass
        try:
            parsed.append((datetime.datetime.strptime(d, "%d.%m.%Y"), d))
        except Exception:
            pass
    if not parsed:
        return ""
    return max(parsed, key=lambda x: x[0])[1]
# ──────────────────────────────────────────────────────────────────────────────
# КЛАССИФИКАЦИЯ ТОПЛИВА
# ──────────────────────────────────────────────────────────────────────────────
FUEL_TYPES = {
    'Бензин': ['бензин', 'аи-92', 'аи-95', 'аи-98', 'аи-100', 'регуляр', 'премиум',
               'евро-92', 'экто-92', 'евро-95', 'экто-95', 'евро-98', 'экто-98'],
    'ДтА':   ['дт-а-к5', 'дт-а к5', '(дт-а)', 'класс 4', 'вид 4', 'арктич', 'минус 44', 'минус 45', 'минус 50', 'минус 52', 'дта'],
    'ДтЗ':   ['дт-з-к5', 'дт-з к5', '(дт-з)', 'класс 0', 'класс 1', 'класс 2', 'класс 3', 'зимн', 'минус 20', 'минус 26', 'минус 32', 'минус 35', 'минус 38', 'дтз'],
    'ДтЕ':   ['дт-е-к5', 'дт-е к5', '(дт-е)', 'сорт e', 'сорт е', 'сорт f', 'минус 15',
               'межсезон'],   # ← Лукойл ЛИКАРД: «ДТ ЕВРО межсезонное», «ДТ ЭКТО межсезонное»
    'ДтЛ':   ['дт-л-к5', 'дт-л к5', '(дт-л)', 'сорт c', 'сорт с', 'сорт d', 'летн', 'дтл',
              'дизельное топливо евро, летнее'],
    'СУГ':   ['суг', 'пропан', 'бутан', 'lpg', 'сжиж'],
}

# Порядок проверки: от наиболее специфичных к общим
# ВАЖНО: 'евро' убран из Бензин — оно встречается и в дизельных названиях
_CAT_CHECK_ORDER = ["ДтА", "ДтЗ", "ДтЕ", "ДтЛ", "Бензин", "СУГ"]
_CAT_ORDER       = ["Бензин", "ДтЛ", "ДтЕ", "ДтЗ", "ДтА", "СУГ"]


# ──────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ──────────────────────────────────────────────────────────────────────────────
def normalize_code(code):
    if code is None:
        return ""
    if not isinstance(code, str):
        code = str(code)
    code = code.upper().strip().replace('"', "").replace("\n", "")
    repls = {"А":"A","В":"B","Е":"E","К":"K","М":"M","Н":"H","О":"O","Р":"P","С":"C","Т":"T","Х":"X","У":"Y"}
    return "".join([repls.get(c, c) for c in code])


def parse_coordinates(coord_str):
    try:
        value = float(str(coord_str).replace(",", ".").strip())
        return value if math.isfinite(value) else None
    except Exception:
        return None


def clean_price(value):
    try:
        s = str(value).strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
        v = float(s)
        return v if v > 0 else None
    except Exception:
        return None


def format_price(price):
    if price is None:
        return "—"
    return f"{price:,.0f}".replace(",", " ") + " ₽"


def get_fuel_category(fuel_name):
    if pd.isna(fuel_name) or not fuel_name:
        return None
    s = str(fuel_name).lower()
    # Перебираем в фиксированном порядке: специфичные ДТ-типы раньше бензина
    # чтобы "дт евро сорт c (дт-л-к5)" не попало в Бензин через слово "евро"
    for cat in _CAT_CHECK_ORDER:
        if any(kw in s for kw in FUEL_TYPES[cat]):
            return cat
    return None


def add_map_layers(map_obj):
    folium.TileLayer('openstreetmap').add_to(map_obj)

def get_fuel_style(fuel_type):
    cat = get_fuel_category(fuel_type)
    mapping = {
        "Бензин":  ("red",       "fire"),
        "ДтЛ":     ("blue",      "tint"),
        "ДтЕ":     ("orange",    "tint"),
        "ДтЗ":     ("lightblue", "tint"),
        "ДтА":     ("cadetblue", "snowflake"),
        "СУГ":     ("purple",    "leaf"),
    }
    return mapping.get(cat, ("gray", "info-sign"))


# Иконка маркера зависит от поставщика (уникальный значок) + цвет от топлива
COMPANY_ICONS = {
    "spimex":      "university",   # 🏛 биржа — колонны
    "lukoil_spot": "tint",         # белая капля на красном
    "lukoil_term": "tint",         # чёрная капля на красном
    "rosneft":     "map-marker",   # кастомная иконка Роснефть
    "other":       "map-marker",   # Транзит Сити и прочие
}

def get_marker_style(fuel_type, company):
    cat = get_fuel_category(fuel_type)
    color_map = {
        "Бензин":  "red",
        "ДтЛ":     "blue",
        "ДтЕ":     "orange",
        "ДтЗ":     "lightblue",
        "ДтА":     "cadetblue",
        "СУГ":     "purple",
    }
    # Лукойл всегда красный, иконка — капля (tint)
    if company == "lukoil_spot":
        return "red", "tint"
    if company == "lukoil_term":
        return "darkred", "tint"
    color = color_map.get(cat, "gray")
    icon  = COMPANY_ICONS.get(company, "map-marker")
    return color, icon


def get_file_date_short(filepath):
    basename = os.path.basename(filepath)
    match = re.search(r'(\d{4})(\d{2})(\d{2})', basename)
    if match:
        return f"{match.group(3)}.{match.group(2)}.{match.group(1)}"
    match = re.search(r'(\d{2})[._-](\d{2})[._-](\d{4})', basename)
    if match:
        return f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
    match = re.search(r'(\d{2})[._](\d{2})', basename)
    if match:
        return f"{match.group(1)}.{match.group(2)}.{datetime.datetime.now().year}"
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(mtime).strftime("%d.%m.%Y")
    except:
        return ""


def _extract_file_date(filepath):
    basename = os.path.basename(filepath)
    match = re.search(r'(\d{4})(\d{2})(\d{2})', basename)
    if match:
        try:
            return datetime.datetime.strptime(match.group(0), "%Y%m%d")
        except Exception:
            pass
    match = re.search(r'(\d{2})[._-](\d{2})[._-](\d{4})', basename)
    if match:
        try:
            return datetime.datetime.strptime(
                f"{match.group(1)}.{match.group(2)}.{match.group(3)}", "%d.%m.%Y"
            )
        except Exception:
            pass
    match = re.search(r'(\d{2})[._](\d{2})', basename)
    if match:
        try:
            return datetime.datetime.strptime(
                f"{match.group(1)}.{match.group(2)}.{datetime.datetime.now().year}",
                "%d.%m.%Y"
            )
        except Exception:
            pass
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
    except Exception:
        return datetime.datetime.min


def pick_latest_files(files, label=""):
    unique_files = sorted(set(files))
    if not unique_files:
        return []
    latest = max(unique_files, key=lambda path: (_extract_file_date(path), os.path.basename(path).lower()))
    if label and len(unique_files) > 1:
        print(f"ℹ️ {label}: найдено {len(unique_files)} файлов, использую самый свежий {os.path.basename(latest)}")
    return [latest]


def _coord_key(lat, lon, precision=5):
    return (round(float(lat), precision), round(float(lon), precision))


def aggregate_markers_by_coordinates(markers, precision=5, company=""):
    buckets = defaultdict(list)
    for m in markers:
        if m.get("lat") is None or m.get("lon") is None:
            continue
        buckets[_coord_key(m["lat"], m["lon"], precision)].append(m)

    out = []
    for (lat_r, lon_r), items in buckets.items():
        names = [str(x.get("name","")).strip() for x in items if str(x.get("name","")).strip()]
        uniq_names = []
        for n in names:
            if n not in uniq_names:
                uniq_names.append(n)
        if not uniq_names:
            merged_name = "Нефтебаза"
        elif len(uniq_names) == 1:
            merged_name = uniq_names[0]
        else:
            merged_name = " / ".join(uniq_names[:2]) + (" …" if len(uniq_names) > 2 else "")

        fuels = []
        seen  = set()
        cats  = set()

        for it in items:
            for f in (it.get("fuels") or []):
                fname  = str(f.get("name","")).strip()
                fprice = f.get("price", None)
                fdate  = f.get("date",  "")
                key    = (fname.lower(), float(fprice) if fprice is not None else None, fdate)
                if key in seen:
                    continue
                seen.add(key)
                cat = f.get("cat") or get_fuel_category(fname)
                fuels.append({"name": fname, "price": fprice, "cat": cat, "date": fdate})
                if cat:
                    cats.add(cat)

        order_index = {c: i for i, c in enumerate(_CAT_ORDER)}
        def _fuel_sort(x):
            c = x.get("cat")
            return (order_index.get(c, 999), str(x.get("name","")).lower())
        fuels.sort(key=_fuel_sort)

        cat_list = sorted(list(cats), key=lambda c: _CAT_ORDER.index(c) if c in _CAT_ORDER else 999)

        # get_marker_style возвращает цвет+иконку с учётом приоритета поставщика:
        # — Лукойл Спот/Терм → всегда красный/тёмно-красный, независимо от топлива
        # — Биржа/другие     → цвет по категории топлива (серый если смешанные)
        first_fuel = fuels[0]["name"] if fuels else ""
        if company in ("lukoil_spot", "lukoil_term"):
            color, icon = get_marker_style(first_fuel, company)
        elif len(cat_list) == 1:
            color, icon = get_marker_style(first_fuel, company)
        else:
            _, icon = get_marker_style(first_fuel, company)
            color = "gray"

        merged_code = "PT_{:.5f}_{:.5f}".format(lat_r, lon_r).replace(".", "_")

        # Сохраняем sections если все элементы — одна объединённая станция
        merged_sections = None
        if len(items) == 1 and items[0].get("sections"):
            merged_sections = items[0]["sections"]

        entry = {
            "code":       merged_code,
            "name":       merged_name,
            "lat":        float(items[0]["lat"]),
            "lon":        float(items[0]["lon"]),
            "fuels":      fuels,
            "color":      color,
            "icon":       icon,
            "categories": cat_list,
        }
        if merged_sections:
            entry["sections"] = merged_sections
            entry["_merged"]  = True
        out.append(entry)

    return out



def _fuel_rows_html(fuels):
    """Генерирует строки таблицы топлива для попапа."""
    if not fuels:
        return '<tr><td style="padding: 4px 0; color:#777;">Нет цен</td><td></td></tr>'
    html = ""
    for fuel in fuels:
        dot_color = get_fuel_style(fuel["name"])[0]
        color_hex = {
            "red":"#dc3545","blue":"#0d6efd","orange":"#fd7e14",
            "lightblue":"#0dcaf0","cadetblue":"#20c997","purple":"#6f42c1","gray":"#adb5bd"
        }.get(dot_color, "#adb5bd")
        date_badge = (
            '<span style="background:#f1f3f5;color:#6c757d;border:1px solid #dee2e6;'
            'padding:2px 6px;border-radius:4px;font-size:10px;margin-right:8px;">'
            + str(fuel["date"]) + '</span>'
        ) if fuel.get("date") else ""
        fuel_price_raw = fuel["price"] if fuel["price"] is not None else ""
        html += (
            '<tr style="border-bottom: 1px solid #f9f9f9;">'
            '<td style="padding: 6px 0; font-size: 12px; vertical-align: middle;">'
            f'<span style="color: {color_hex}; font-size: 14px; margin-right: 4px;">●</span>{fuel["name"]}'
            '</td>'
            f'<td style="text-align: right; font-weight: bold; color: #007bff; font-size: 14px; white-space: nowrap; vertical-align: middle;" data-base-price="{fuel_price_raw}">'
            f'{date_badge}{format_price(fuel["price"])}'
            '</td></tr>'
        )
    return html


def merge_lukoil_layers(spot_raw, term_raw, precision=4):
    """Объединяет Спот и Терм. Совпадающие нефтебазы → один маркер с sections."""
    def ck(m): return _coord_key(m["lat"], m["lon"], precision)
    def nk(m): return _norm_name(m.get("name", ""))

    term_by_coord, term_by_name = {}, {}
    for t in term_raw:
        term_by_coord.setdefault(ck(t), []).append(t)
        term_by_name.setdefault(nk(t),  []).append(t)

    used_term, results = set(), []
    for spot in spot_raw:
        matches = term_by_coord.get(ck(spot)) or term_by_name.get(nk(spot)) or []
        matches = [t for t in matches if id(t) not in used_term]
        spot_fuels = spot.get("fuels", [])
        term_fuels = []
        for t in matches:
            term_fuels.extend(t.get("fuels", []))
            used_term.add(id(t))
        if term_fuels:
            results.append({"code": spot.get("code",""), "name": spot.get("name",""),
                "lat": spot["lat"], "lon": spot["lon"], "_merged": True,
                "fuels": spot_fuels + term_fuels,
                "sections": [{"label":"Лукойл Спот","fuels":spot_fuels},
                             {"label":"Лукойл Терм","fuels":term_fuels}]})
        else:
            spot["sections"] = [{"label":"Лукойл Спот","fuels":spot_fuels}]
            results.append(spot)
    for t in term_raw:
        if id(t) not in used_term:
            t["sections"] = [{"label":"Лукойл Терм","fuels":t.get("fuels",[])}]
            results.append(t)
    return results

# ──────────────────────────────────────────────────────────────────────────────
# POPUP HTML
# ──────────────────────────────────────────────────────────────────────────────
def create_popup_html(data, company):
    safe_name = str(data["name"]).replace("'", "\\'").replace('"', '&quot;')

    company_labels = {
        "spimex":      "Петербургская биржа",
        "lukoil_spot": "Лукойл Спот",
        "lukoil_term": "Лукойл Терм",
        "rosneft":     "Роснефть",
        "other":       "Транзит Сити",
    }
    sections  = data.get("sections")
    comp_name = "Лукойл Спот + Терм" if sections else company_labels.get(company, "Поставщики")

    # Проверяем — является ли эта нефтебаза ОТП (по ключевым словам)
    otp_keys = [
        'лпдс володарская','нс солнечногорская','нс нагорная','лпдс сокур',
        'лпдс невская','лпдс черкассы','лпдс никольское-1','нп брянск',
        'лпдс воронеж','лпдс белгород'
    ]
    station_lower = data["name"].lower()
    is_otp = any(k in station_lower for k in otp_keys)

    html = f"""
    <div style="font-family: Arial, sans-serif; width: 360px; font-size: 13px; padding: 14px 16px 0 16px; box-sizing: border-box;">
        <div style="font-size: 10px; color: #888; text-transform: uppercase; letter-spacing:.05em; margin-bottom: 4px;">{comp_name}</div>
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 10px; border-bottom: 1px solid #f0f0f0; padding-bottom: 8px;">
            {data["name"]}
        </div>
    """

    if sections:
        for sec in sections:
            if not sec.get("fuels"):
                continue
            label = sec["label"]
            lcolor = "#dc3545" if "Спот" in label else "#8b0000"
            html += (
                f'<div style="font-size:10px;font-weight:700;color:{lcolor};'
                f'text-transform:uppercase;letter-spacing:.06em;margin:8px 0 4px 0;'
                f'padding-bottom:3px;border-bottom:2px solid {lcolor}44;">{label}</div>'
                f'<table style="width:100%;border-collapse:collapse;margin-bottom:6px;">'
            )
            html += _fuel_rows_html(sec["fuels"])
            html += "</table>"
    else:
        _code = data.get("code", "")
        html += f'<table style="width:100%;border-collapse:collapse;margin-bottom:10px;" id="fuelTable-{_code}">'
        html += _fuel_rows_html(data.get("fuels", []))
        html += "</table>"

    html += "    "

    # Для ОТП-нефтебаз — блок с надбавками (заполняется JS при открытии попапа)
    if is_otp:
        html += f"""
        <div id="otp-surcharge-{data['code']}" style="
            background:#fff8e1; border:1px solid #ffe082; border-radius:8px;
            padding:8px 10px; margin-bottom:10px; font-size:11px;
        ">
            <div style="font-weight:600;color:#f57c00;margin-bottom:4px;">⚙ Услуги ОТП (ФР)</div>
            <div id="otp-detail-{data['code']}" style="color:#555;line-height:1.8;">
                <!-- заполняется JS -->
            </div>
        </div>
        """

    html += f"""
        <div id="delivery-{data["code"]}" class="popup-delivery-zone">
            <button class="delivery-btn"
                    style="background:#000;color:#fff;border:none;padding:6px 12px;font-size:11px;cursor:pointer;font-family:Arial;width:100%;"
                    onclick="event.stopPropagation(); var W=(window.parent||window); W.startDelivery('{data['code']}', {data['lat']}, {data['lon']}, '{safe_name}')">
                РАССЧИТАТЬ ЛОГИСТИКУ
            </button>
        </div>
    </div>
    """
    return html


# ──────────────────────────────────────────────────────────────────────────────
# UI PANEL
# ──────────────────────────────────────────────────────────────────────────────
def create_ui(provider_dates, otp_prices=None):
    if otp_prices is None:
        otp_prices = {k: {"nalyv": 0, "storage": 0} for k in OTP_STATION_KEYS}
    otp_prices_json = json.dumps(otp_prices, ensure_ascii=False)
    # Вспомогательная функция: подпись с датой под названием поставщика
    def _dsub(key):
        d = provider_dates.get(key, "") if isinstance(provider_dates, dict) else ""
        return (f'<br><span style="font-size:9px;color:#aaa;line-height:1.6;font-weight:400;">{d}</span>'
                if d else "")
    d_spimex = _dsub("spimex")
    d_spot   = _dsub("lukoil_spot")
    d_term   = _dsub("lukoil_term")
    d_rosn   = _dsub("rosneft")
    d_other  = _dsub("other")
    return f"""
<style>
  .leaflet-container {{ font-family: Arial, sans-serif !important; }}

  .mono-fab {{
    position: fixed; z-index: 9999; top: 6px; left: 6px;
    width: 44px; height: 44px; background: #111; color: #fff;
    border-radius: 50%; display: none; align-items: center; justify-content: center;
    cursor: pointer; box-shadow: 4px 4px 0 rgba(0,0,0,0.1);
    font-size: 20px; font-weight: bold; border: 2px solid #fff; user-select: none;
  }}
  .mono-fab:active {{ transform: translateY(2px); }}

  .mono-panel {{
    position: fixed; z-index: 9998; top: 6px; left: 6px; width: 300px;
    background: #fff; border: 1px solid #111;
    box-shadow: 8px 8px 0 rgba(0,0,0,0.06);
    border-radius: 12px; overflow: hidden; user-select: none;
    max-height: calc(100vh - 12px); display: flex; flex-direction: column;
  }}
  .mono-header {{
    background: #111; color: #fff; padding: 10px 12px;
    font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    display: flex; align-items: center; justify-content: space-between; cursor: move;
    flex-shrink: 0;
  }}
  .mono-toggle {{
    cursor: pointer; font-weight: 700; padding: 2px 8px;
    border: 1px solid rgba(255,255,255,.25); border-radius: 999px; transition: 0.2s;
  }}
  .mono-toggle:hover {{ background: rgba(255,255,255,0.2); }}

  .mono-scroll {{ overflow-y: auto; flex: 1; }}
  .mono-content {{ padding: 12px; font-size: 12px; border-top: 1px solid #111; }}
  .mono-muted {{ color:#666; font-size: 11px; line-height: 1.4; }}
  .mono-block {{ padding: 10px; border: 1px solid #eee; border-radius: 12px; margin-top: 10px; }}
  .mono-row {{ display:flex; gap:8px; }}
  .mono-row > * {{ flex:1; }}
  .mono-input {{
    width: 100%; padding: 7px 10px; border: 1px solid #ddd;
    border-radius: 12px; outline: none; font-size: 12px; box-sizing: border-box;
  }}
  .mono-btn {{
    background: #111; color: #fff; border: 0; padding: 8px 10px;
    border-radius: 12px; cursor: pointer; font-size: 11px;
    letter-spacing: .04em; text-transform: uppercase; white-space: nowrap;
  }}
  .mono-btn:active {{ transform: translateY(1px); }}
  .mono-btn--ghost {{
    background: #fff !important; color:#111 !important; border:1px solid #111 !important;
  }}
  .mono-btn--sm {{ padding: 5px 8px !important; font-size: 10px !important; }}
  .mono-checks {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px 10px; margin-top: 8px; }}
  .mono-check {{ display:flex; align-items:center; gap: 6px; font-size: 12px; color:#111; }}
  .legend {{ display:grid; grid-template-columns: 1fr 1fr; gap: 6px 10px; margin-top: 8px; font-size: 11px; color:#333; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; display:inline-block; border: 1px solid rgba(0,0,0,.15); }}
  .result-box {{
    margin-top: 10px; padding: 10px; background: #f6f8ff;
    border: 1px dashed #cfd6ff; border-radius: 12px; font-size: 11px; line-height: 1.6;
  }}
  .wp-item {{ display:flex; align-items:center; gap:6px; margin-top:5px; font-size:11px; }}
  .wp-dot  {{ width:8px; height:8px; border-radius:50%; background:#007bff; flex-shrink:0; }}
  .wp-del  {{
    margin-left:auto; cursor:pointer; color:#dc3545; font-weight:bold;
    background:none; border:none; font-size:13px; line-height:1; padding:0;
  }}
  .popup-delivery-zone {{
    background:#fff; padding:10px 16px 14px; border-top:1px solid #f0f0f0; text-align:center; margin-top:4px;
  }}
  .finder-fuel-btn {{
    display:inline-block; margin:4px; padding:7px 14px;
    border:1.5px solid #111; border-radius:20px; cursor:pointer;
    font-size:12px; font-family:Arial; background:#fff;
    transition: background 0.15s, color 0.15s;
  }}
  .finder-fuel-btn:hover {{ background:#111; color:#fff; }}
  .finder-fuel-btn.active {{ background:#111; color:#fff; }}
  .finder-result-row {{
    background:#f8f9fa; border-radius:10px; padding:10px 12px; margin-top:8px;
    border-left:4px solid #007bff;
  }}
  .finder-result-row.best {{ border-left-color:#28a745; background:#f0fff4; }}
  .finder-route-line-1 {{ stroke:#28a745; }}
  .finder-route-line-2 {{ stroke:#fd7e14; }}
  .finder-route-line-3 {{ stroke:#6f42c1; }}

  /* Попап без iframe — прямой JS bindPopup */
  .custom-popup .leaflet-popup-content-wrapper {{
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.18);
    padding: 0;
    overflow: hidden;
    border: none;
    background: #fff;
  }}
  .custom-popup .leaflet-popup-content {{
    margin: 0;
    padding: 0;
    width: auto !important;
    line-height: 1.5;
  }}
  .custom-popup .leaflet-popup-tip-container,
  .custom-popup .leaflet-popup-tip {{
    display: none !important;
  }}
  .custom-popup {{
    margin-bottom: 0;
  }}
  /* Сброс дефолтного outline Leaflet при клике */
  .leaflet-container a.leaflet-popup-close-button {{
    top: 8px; right: 10px; color: #aaa; font-size: 18px; font-weight: 300;
  }}
  .leaflet-container a.leaflet-popup-close-button:hover {{ color: #333; }}
</style>

<div class="mono-fab" id="restoreBtn" onclick="restorePanel()" title="Открыть меню">☰</div>

<div class="mono-panel" id="uiPanel">
  <div class="mono-header" id="uiHeader">
    <span>Меню</span>
    <span class="mono-toggle" onclick="minimizePanel()" title="Скрыть">×</span>
  </div>
  <div class="mono-scroll">
  <div class="mono-content" id="uiContent">
    <div class="mono-block">
      <div style="font-weight:700;font-size:12px;margin-bottom:6px;">Поиск нефтебаз</div>
      <div class="mono-row">
        <input id="searchInput" class="mono-input" placeholder="Название или код..." />
        <button class="mono-btn" onclick="searchStation()">Найти</button>
      </div>
      <div class="mono-muted" style="margin-top:5px;">Enter — поиск</div>
    </div>

    <div class="mono-block">
      <div style="font-weight:700;font-size:12px;margin-bottom:6px;">Фильтры</div>
      <div class="mono-muted">Поставщики</div>
      <div class="mono-checks" style="margin-top:6px;">
        <label class="mono-check"><input type="checkbox" id="flt_spimex" checked onchange="applyFilters()">
          <span style="width:10px;height:10px;border-radius:3px;background:#6c757d;display:inline-block;flex-shrink:0;margin-top:2px;"></span>
          <span>СПб биржа{d_spimex}</span></label>
        <label class="mono-check"><input type="checkbox" id="flt_lukoil_spot" checked onchange="applyFilters()">
          <span style="width:10px;height:10px;border-radius:3px;background:#dc3545;display:inline-block;flex-shrink:0;margin-top:2px;"></span>
          <span>Лукойл Спот{d_spot}</span></label>
        <label class="mono-check"><input type="checkbox" id="flt_lukoil_term" checked onchange="applyFilters()">
          <span style="width:10px;height:10px;border-radius:3px;background:#8b0000;display:inline-block;flex-shrink:0;margin-top:2px;"></span>
          <span>Лукойл Терм{d_term}</span></label>
        <label class="mono-check"><input type="checkbox" id="flt_rosneft" checked onchange="applyFilters()">
          <span style="width:10px;height:10px;border-radius:3px;background:#212529;display:inline-block;flex-shrink:0;margin-top:2px;"></span>
          <span>Роснефть{d_rosn}</span></label>
        <label class="mono-check"><input type="checkbox" id="flt_other" checked onchange="applyFilters()">
          <span style="width:10px;height:10px;border-radius:3px;background:#adb5bd;display:inline-block;flex-shrink:0;margin-top:2px;"></span>
          <span>Транзит Сити{d_other}</span></label>
      </div>
      <div class="mono-muted" style="margin-top:10px;">Топливо <span style="color:#bbb;font-size:10px;">(цвет маркера на карте)</span></div>
      <div class="mono-checks" style="margin-top:6px;">
        <label class="mono-check"><input type="checkbox" id="flt_Benz" checked onchange="applyFilters()">
          <span class="dot" style="background:#dc3545;"></span> Бензин</label>
        <label class="mono-check"><input type="checkbox" id="flt_DtL"  checked onchange="applyFilters()">
          <span class="dot" style="background:#0d6efd;"></span> ДтЛ</label>
        <label class="mono-check"><input type="checkbox" id="flt_DtE"  checked onchange="applyFilters()">
          <span class="dot" style="background:#fd7e14;"></span> ДтЕ</label>
        <label class="mono-check"><input type="checkbox" id="flt_DtZ"  checked onchange="applyFilters()">
          <span class="dot" style="background:#0dcaf0;"></span> ДтЗ</label>
        <label class="mono-check"><input type="checkbox" id="flt_DtA"  checked onchange="applyFilters()">
          <span class="dot" style="background:#20c997;"></span> ДтА</label>
        <label class="mono-check"><input type="checkbox" id="flt_SUG"  checked onchange="applyFilters()">
          <span class="dot" style="background:#6f42c1;"></span> СУГ</label>
      </div>
    </div>

    <div class="mono-block">
      <div style="font-weight:700;font-size:12px;margin-bottom:8px;">Параметры перевозки</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
        <div>
          <div class="mono-muted" style="margin-bottom:3px;">Тариф, ₽/км</div>
          <input id="tariffInput" class="mono-input" type="number" min="1" value="{TARIFF_PER_KM}" />
        </div>
        <div>
          <div class="mono-muted" style="margin-bottom:3px;">Тоннаж, т</div>
          <input id="tonnageInput" class="mono-input" type="number" min="1" value="{TRUCK_TONS}" />
        </div>
      </div>
      <div class="mono-muted" style="margin-top:6px;">Применяются при каждом расчёте</div>
    </div>

    <div class="mono-block">
      <div style="font-weight:700;font-size:12px;margin-bottom:6px;">Логистика (до 10 точек)</div>
      <div class="mono-muted">
        1) Нажмите <b>«РАССЧИТАТЬ ЛОГИСТИКУ»</b> в попапе нефтебазы<br>
        2) Кликайте на карте (или нажмите <b>«+ Точка»</b>) — добавляются точки маршрута<br>
        3) <b>Shift+Click</b> (ПК) или кнопка <b>«Построить маршрут»</b> — строит маршрут<br>
        4) Или нажмите <b>«Построить маршрут»</b>
      </div>

      <div id="waypointList" style="margin-top:8px;"></div>

      <div style="margin-top:8px;">
        <button class="mono-btn" onclick="buildMultiRoute()" id="buildBtn" style="display:none;width:100%;">Построить маршрут</button>
      </div>
      <div class="mono-row" style="margin-top:6px; gap:6px;">
        <button class="mono-btn mono-btn--ghost mono-btn--sm" id="addPointBtn"
                style="display:none;" onclick="addPointFromCenter()">+ Точка</button>
        <button class="mono-btn mono-btn--ghost mono-btn--sm" onclick="clearRouteOnly()">Убрать маршрут</button>
        <button class="mono-btn mono-btn--ghost mono-btn--sm" onclick="clearLogistics()">Сбросить всё</button>
      </div>

      <div id="calcStatus" class="result-box" style="margin-top:8px;">
        Выберите станцию для расчёта
      </div>
    </div>

    <div class="mono-block">
      <div style="font-weight:700;font-size:12px;margin-bottom:6px;">Найти лучшую цену</div>
      <div class="mono-muted" style="margin-bottom:8px;">
        <b>ПК:</b> Alt+Click на карте.&nbsp;
        <b>Телефон:</b> нажмите кнопку ниже, затем тапните на карте.
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <div style="flex:1;">
          <div class="mono-muted" style="margin-bottom:3px;">Радиус поиска, км</div>
          <input id="finderRadiusInput" class="mono-input" type="number" min="50" max="2000" value="300" />
        </div>
        <div style="flex:1;padding-top:18px;">
          <button class="mono-btn mono-btn--ghost mono-btn--sm" style="width:100%;" onclick="exitFinderMode()">✕ Выйти</button>
        </div>
      </div>
      <button id="mobileFindBtn" class="mono-btn" style="width:100%;margin-bottom:6px;background:#007bff;"
              onclick="activateMobileFinder()">🔍 Лучшая цена с доставкой</button>
      <div id="finderStatus" class="mono-muted" style="color:#007bff;"></div>
    </div>

    <div class="mono-block">
      <div style="font-weight:700;font-size:12px;margin-bottom:6px;">Услуги ОТП (ЛПДС / НС / НП)</div>
      <div class="mono-muted" style="margin-bottom:8px;">Надбавки за налив и хранение учитываются в попапах и при расчёте лучшей цены</div>
      <button class="mono-btn" style="width:100%;" onclick="openOtpModal()">⚙ Настроить надбавки ОТП</button>
    </div>

  </div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════════════
     ФИНДЕР — боковая панель поверх карты (не модалка)
     ════════════════════════════════════════════════════════════ -->
<div id="finderPanel" style="
  display:none; position:fixed; z-index:10500;
  top:18px; right:18px; width:340px;
  background:#fff; border:1px solid #111; border-radius:14px;
  box-shadow:8px 8px 0 rgba(0,0,0,0.07); font-family:Arial,sans-serif;
  font-size:12px; max-height:calc(100vh - 36px); display:none; flex-direction:column;
">
  <!-- шапка -->
  <div style="background:#111;color:#fff;padding:10px 14px;border-radius:13px 13px 0 0;
              display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">
    <span style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;">
      🔍 Лучшая цена с доставкой
    </span>
    <span onclick="closeFinderPanel()"
          style="cursor:pointer;font-weight:700;padding:2px 8px;border:1px solid rgba(255,255,255,.3);
                 border-radius:999px;font-size:13px;">×</span>
  </div>

  <!-- прокручиваемое тело -->
  <div style="overflow-y:auto;flex:1;padding:12px;">
    <div id="finderCoords" style="color:#666;font-size:11px;margin-bottom:8px;"></div>

    <!-- выбор топлива: полный список -->
    <div id="finderFuelSection">
      <div style="font-weight:700;margin-bottom:6px;">Выберите вид топлива:</div>
      <div id="finderFuelBtns"></div>
    </div>

    <!-- выбор топлива: свёрнутое состояние (после выбора) -->
    <div id="finderFuelChosen" style="display:none;margin-bottom:8px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <span id="finderFuelChosenLabel" style="
          display:inline-block;background:#111;color:#fff;
          padding:5px 14px;border-radius:20px;font-size:12px;font-weight:600;
        "></span>
        <button onclick="expandFinderFuel()" style="
          background:#fff;border:1px solid #bbb;color:#555;
          padding:4px 10px;border-radius:20px;font-size:11px;cursor:pointer;
        ">✎ изменить</button>
      </div>
    </div>

    <!-- статус загрузки -->
    <div id="finderLoader" style="display:none;text-align:center;padding:20px 0;color:#666;">
      <div style="font-size:22px;margin-bottom:6px;">⏳</div>
      <div>Строю маршруты по дорогам…</div>
      <div id="finderLoaderSub" style="font-size:10px;margin-top:4px;color:#aaa;"></div>
    </div>

    <!-- результаты -->
    <div id="finderResults"></div>

    <!-- кнопки -->
    <div id="finderActions" style="display:none;margin-top:10px;display:none;gap:6px;flex-wrap:wrap;">
      <button class="mono-btn mono-btn--ghost mono-btn--sm" onclick="clearFinderRoutes()" style="flex:1;">Убрать маршруты</button>
      <button class="mono-btn mono-btn--ghost mono-btn--sm" onclick="closeFinderPanel()" style="flex:1;">Закрыть</button>
    </div>
  </div>
</div>

<!-- ════════════════════════════════════════════════════════════
     ОТП — модальное окно с надбавками по каждой нефтебазе
     ════════════════════════════════════════════════════════════ -->
<div id="otpModal" style="
  display:none; position:fixed; z-index:12000; top:0; left:0; width:100%; height:100%;
  background:rgba(0,0,0,0.5); align-items:center; justify-content:center;
" onclick="if(event.target===this)closeOtpModal()">
  <div style="
    background:#fff; border-radius:16px; padding:0;
    width:560px; max-width:96vw; max-height:90vh;
    box-shadow:0 12px 40px rgba(0,0,0,0.2);
    font-family:Arial,sans-serif; display:flex; flex-direction:column;
  ">
    <!-- шапка -->
    <div style="background:#111;color:#fff;padding:14px 20px;border-radius:15px 15px 0 0;
                display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">
      <span style="font-size:13px;font-weight:700;letter-spacing:.05em;">⚙ Надбавки ОТП — налив и хранение</span>
      <span onclick="closeOtpModal()" style="cursor:pointer;font-size:18px;padding:0 6px;
             border:1px solid rgba(255,255,255,.3);border-radius:999px;">×</span>
    </div>
    <!-- описание -->
    <div style="padding:12px 20px 0;font-size:11px;color:#666;flex-shrink:0;">
      Укажите надбавки ₽/тонну для каждой нефтебазы. Сумма (налив + хранение) прибавляется к цене топлива в попапе и при расчёте лучшей цены.
    </div>
    <!-- таблица (скроллируемая) -->
    <div style="overflow-y:auto;flex:1;padding:12px 20px;">
      <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <thead>
          <tr style="border-bottom:2px solid #111;">
            <th style="text-align:left;padding:8px 6px;font-size:11px;color:#555;font-weight:600;">Нефтебаза</th>
            <th style="text-align:center;padding:8px 6px;font-size:11px;color:#555;font-weight:600;width:130px;">Налив, ₽/т</th>
            <th style="text-align:center;padding:8px 6px;font-size:11px;color:#555;font-weight:600;width:130px;">Хранение 5 дн., ₽/т</th>
            <th style="text-align:center;padding:8px 6px;font-size:11px;color:#555;font-weight:600;width:100px;">Сумма, ₽/т</th>
          </tr>
        </thead>
        <tbody id="otpTableBody"></tbody>
      </table>
    </div>
    <!-- кнопки -->
    <div style="padding:12px 20px 16px;display:flex;gap:8px;flex-shrink:0;border-top:1px solid #eee;flex-wrap:wrap;">
      <button onclick="saveOtpPrices()" style="
        flex:1;background:#111;color:#fff;border:none;padding:10px;
        border-radius:10px;cursor:pointer;font-size:12px;font-weight:600;min-width:120px;
      ">💾 Сохранить</button>
      <button onclick="downloadOtpFile()" style="
        background:#fff;color:#111;border:1px solid #111;padding:10px 14px;
        border-radius:10px;cursor:pointer;font-size:12px;
      ">⬇ stavkiOTP.txt</button>
      <button onclick="resetOtpPrices()" style="
        background:#fff;color:#dc3545;border:1px solid #dc3545;padding:10px 14px;
        border-radius:10px;cursor:pointer;font-size:12px;
      ">Сбросить</button>
      <button onclick="closeOtpModal()" style="
        background:#fff;color:#666;border:1px solid #ddd;padding:10px 14px;
        border-radius:10px;cursor:pointer;font-size:12px;
      ">Закрыть</button>
    </div>
  </div>
</div>

<script>
// ── глобальное состояние ──────────────────────────────────────────────────────
let mapInst        = null;
let routingControl = null;
let activeDelivery = {{ code:null, lat:null, lon:null, name:null }};
let waypoints      = [];          // [{{lat, lon, marker}}]
let collectingWpts = false;
let lastRoutePopupCode = null;
const LOCAL_VENDOR = {{
  routingCss: 'assets/vendor/leaflet-routing-machine/leaflet-routing-machine.css',
  routingJs: 'assets/vendor/leaflet-routing-machine/leaflet-routing-machine.js',
  omsJs: 'assets/vendor/oms/oms.min.js'
}};
window.__vendorPromises__ = window.__vendorPromises__ || {{}};

function loadCssOnce(href) {{
  if (!href) return Promise.resolve();
  if (document.querySelector(`link[href="${{href}}"]`)) return Promise.resolve();
  return new Promise((resolve, reject) => {{
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.onload = resolve;
    link.onerror = () => reject(new Error(`CSS load failed: ${{href}}`));
    document.head.appendChild(link);
  }});
}}

function loadScriptOnce(src) {{
  if (!src) return Promise.resolve();
  if (window.__vendorPromises__[src]) return window.__vendorPromises__[src];
  const existing = document.querySelector(`script[src="${{src}}"]`);
  if (existing) {{
    window.__vendorPromises__[src] = new Promise((resolve, reject) => {{
      if (existing.dataset.loaded === '1') {{
        resolve();
        return;
      }}
      existing.addEventListener('load', () => {{
        existing.dataset.loaded = '1';
        resolve();
      }}, {{ once: true }});
      existing.addEventListener('error', () => reject(new Error(`Script load failed: ${{src}}`)), {{ once: true }});
    }});
    return window.__vendorPromises__[src];
  }}
  window.__vendorPromises__[src] = new Promise((resolve, reject) => {{
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => {{
      script.dataset.loaded = '1';
      resolve();
    }};
    script.onerror = () => reject(new Error(`Script load failed: ${{src}}`));
    document.head.appendChild(script);
  }});
  return window.__vendorPromises__[src];
}}

async function ensureRoutingMachine() {{
  if (window.L && window.L.Routing) return;
  await loadCssOnce(LOCAL_VENDOR.routingCss);
  await loadScriptOnce(LOCAL_VENDOR.routingJs);
}}

function initOmsIfReady() {{
  if (window.__OMS__ || !mapInst || !window.OverlappingMarkerSpiderfier) return !!window.__OMS__;
  window.__OMS__ = new OverlappingMarkerSpiderfier(mapInst, {{
    keepSpiderfied: true,
    nearbyDistance: 20,
    legWeight: 1.5,
    circleSpiralSwitchover: 6,
  }});
  window.__OMS__.addListener('click', function(mk) {{ mk.openPopup(); }});
  (window.__OMS_QUEUE__ || []).forEach(mk => window.__OMS__.addMarker(mk));
  window.__OMS_QUEUE__ = [];
  return true;
}}

function warmLoadOms() {{
  if (window.__OMS__ || !mapInst) return;
  loadScriptOnce(LOCAL_VENDOR.omsJs)
    .then(() => initOmsIfReady())
    .catch(err => console.warn('OMS preload failed:', err));
}}

// ── утилиты ──────────────────────────────────────────────────────────────────
function getTariff()  {{ return parseFloat(document.getElementById('tariffInput').value)  || {TARIFF_PER_KM}; }}
function getTonnage() {{ return parseFloat(document.getElementById('tonnageInput').value) || {TRUCK_TONS}; }}
function getFinderRadius() {{ return parseFloat(document.getElementById('finderRadiusInput').value) || 300; }}

// ── ОТП: надбавки по каждой нефтебазе ───────────────────────────────────────
// Список ОТП-нефтебаз: [ключ, отображаемое название]
const OTP_STATIONS_LIST = [
  ['лпдс володарская',    'ЛПДС Володарская'],
  ['нс солнечногорская',  'НС Солнечногорская'],
  ['нс нагорная',         'НС Нагорная'],
  ['лпдс сокур',          'ЛПДС Сокур'],
  ['лпдс невская',        'ЛПДС Невская'],
  ['лпдс черкассы',       'ЛПДС Черкассы'],
  ['лпдс никольское-1',   'ЛПДС Никольское-1'],
  ['нп брянск',           'НП Брянск'],
  ['лпдс воронеж',        'ЛПДС Воронеж'],
  ['лпдс белгород',       'ЛПДС Белгород'],
];

// Хранилище цен — начальные значения из stavkiOTP.txt (вшиты при генерации карты)
const __OTP_FROM_FILE__ = {otp_prices_json};
window.__OTP_PRICES__ = {{}};
OTP_STATIONS_LIST.forEach(([key]) => {{
  window.__OTP_PRICES__[key] = __OTP_FROM_FILE__[key] || {{nalyv: 0, storage: 0}};
}});

// Перекрываем значениями из localStorage (если пользователь редактировал без перегенерации)
(function() {{
  try {{
    const saved = localStorage.getItem('otp_prices_v1');
    if (saved) {{
      const parsed = JSON.parse(saved);
      OTP_STATIONS_LIST.forEach(([key]) => {{
        if (parsed[key]) window.__OTP_PRICES__[key] = parsed[key];
      }});
      console.log('ОТП надбавки загружены из localStorage');
    }}
  }} catch(e) {{ console.warn('Не удалось прочитать localStorage:', e); }}
}})();

// Возвращает суммарную надбавку для нефтебазы по названию
function getOtpSurcharge(stationName) {{
  const n = (stationName||'').toLowerCase();
  for (const [key] of OTP_STATIONS_LIST) {{
    if (n.includes(key)) {{
      const p = window.__OTP_PRICES__[key] || {{nalyv:0, storage:0}};
      return (p.nalyv||0) + (p.storage||0);
    }}
  }}
  return 0;
}}

function getOtpDetail(stationName) {{
  const n = (stationName||'').toLowerCase();
  for (const [key] of OTP_STATIONS_LIST) {{
    if (n.includes(key)) {{
      return window.__OTP_PRICES__[key] || {{nalyv:0, storage:0}};
    }}
  }}
  return null;
}}

function isOtpStation(name) {{ return getOtpSurcharge(name) > 0 || OTP_STATIONS_LIST.some(([k])=>(name||'').toLowerCase().includes(k)); }}

// ── ОТП: управление модальным окном ─────────────────────────────────────────
function openOtpModal() {{
  // Строим строки таблицы
  let rows = '';
  OTP_STATIONS_LIST.forEach(([key, label]) => {{
    const p = window.__OTP_PRICES__[key] || {{nalyv:0, storage:0}};
    const total = (p.nalyv||0) + (p.storage||0);
    rows += `<tr style="border-bottom:1px solid #f0f0f0;" id="otpRow_${{key.replace(/\\s+/g,'_')}}">
      <td style="padding:8px 6px;font-weight:500;">${{label}}</td>
      <td style="padding:8px 6px;text-align:center;">
        <input type="number" min="0" value="${{p.nalyv||0}}"
          style="width:100px;padding:5px 8px;border:1px solid #ddd;border-radius:8px;font-size:12px;text-align:right;"
          oninput="updateOtpTotal('${{key}}')"
          id="otpNalyv_${{key.replace(/\\s+/g,'_')}}" data-key="${{key}}" data-field="nalyv" />
      </td>
      <td style="padding:8px 6px;text-align:center;">
        <input type="number" min="0" value="${{p.storage||0}}"
          style="width:100px;padding:5px 8px;border:1px solid #ddd;border-radius:8px;font-size:12px;text-align:right;"
          oninput="updateOtpTotal('${{key}}')"
          id="otpStorage_${{key.replace(/\\s+/g,'_')}}" data-key="${{key}}" data-field="storage" />
      </td>
      <td style="padding:8px 6px;text-align:center;">
        <span id="otpSum_${{key.replace(/\\s+/g,'_')}}"
          style="font-weight:bold;color:${{total>0?'#e67e22':'#aaa'}};">${{total.toLocaleString()}}</span>
      </td>
    </tr>`;
  }});
  document.getElementById('otpTableBody').innerHTML = rows;
  document.getElementById('otpModal').style.display = 'flex';
}}

function updateOtpTotal(key) {{
  const safeKey = key.replace(/\\s+/g,'_');
  const nalyv   = parseFloat(document.getElementById('otpNalyv_'+safeKey)?.value)   || 0;
  const storage = parseFloat(document.getElementById('otpStorage_'+safeKey)?.value) || 0;
  const total   = nalyv + storage;
  const sumEl   = document.getElementById('otpSum_'+safeKey);
  if (sumEl) {{
    sumEl.textContent = total.toLocaleString();
    sumEl.style.color = total > 0 ? '#e67e22' : '#aaa';
  }}
}}

function saveOtpPrices() {{
  OTP_STATIONS_LIST.forEach(([key]) => {{
    const safeKey = key.replace(/\\s+/g,'_');
    const nalyv   = parseFloat(document.getElementById('otpNalyv_'+safeKey)?.value)   || 0;
    const storage = parseFloat(document.getElementById('otpStorage_'+safeKey)?.value) || 0;
    window.__OTP_PRICES__[key] = {{nalyv, storage}};
  }});
  // Сохраняем в localStorage для работы без перегенерации карты
  try {{
    localStorage.setItem('otp_prices_v1', JSON.stringify(window.__OTP_PRICES__));
  }} catch(e) {{ console.warn('localStorage недоступен:', e); }}
  closeOtpModal();
  document.getElementById('finderStatus').textContent = '✅ Надбавки ОТП сохранены';
  setTimeout(()=>{{ document.getElementById('finderStatus').textContent=window._isMobile() ? 'Долгое нажатие на карте — найти лучшую цену' : 'Alt+Click на карте — найти лучшую цену'; }}, 2500);
}}

function downloadOtpFile() {{
  // Сначала сохраняем текущие значения из формы
  OTP_STATIONS_LIST.forEach(([key]) => {{
    const safeKey = key.replace(/\\s+/g,'_');
    const nalyv   = parseFloat(document.getElementById('otpNalyv_'+safeKey)?.value)   || 0;
    const storage = parseFloat(document.getElementById('otpStorage_'+safeKey)?.value) || 0;
    window.__OTP_PRICES__[key] = {{nalyv, storage}};
  }});
  // Сохраняем в localStorage
  try {{ localStorage.setItem('otp_prices_v1', JSON.stringify(window.__OTP_PRICES__)); }} catch(e) {{}}
  // Скачиваем как JSON (читается при следующей генерации карты map_builder.py)
  const content = JSON.stringify(window.__OTP_PRICES__, null, 2);
  const blob = new Blob([content], {{type:'application/json;charset=utf-8'}});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'stavkiOTP.txt'; a.click();
  URL.revokeObjectURL(url);
}}

function resetOtpPrices() {{
  OTP_STATIONS_LIST.forEach(([key]) => {{
    window.__OTP_PRICES__[key] = {{nalyv:0, storage:0}};
    const safeKey = key.replace(/\\s+/g,'_');
    const ni = document.getElementById('otpNalyv_'+safeKey);
    const si = document.getElementById('otpStorage_'+safeKey);
    if (ni) ni.value = 0;
    if (si) si.value = 0;
    updateOtpTotal(key);
  }});
  try {{ localStorage.removeItem('otp_prices_v1'); }} catch(e) {{}}
}}

function closeOtpModal() {{
  document.getElementById('otpModal').style.display = 'none';
}}

function expandFinderFuel() {{
  document.getElementById('finderFuelChosen').style.display  = 'none';
  document.getElementById('finderFuelSection').style.display = 'block';
  document.getElementById('finderResults').innerHTML = '';
  document.getElementById('finderActions').style.display = 'none';
  clearFinderRoutes();
}}

function collapseFinderFuel(label) {{
  document.getElementById('finderFuelSection').style.display  = 'none';
  document.getElementById('finderFuelChosenLabel').textContent = label;
  document.getElementById('finderFuelChosen').style.display    = 'flex';
}}

function exitFinderMode() {{
  _resetMobileFindBtn();
  if (finderDestMarker) {{ mapInst.removeLayer(finderDestMarker); finderDestMarker=null; }}
  clearFinderRoutes();
  closeFinderPanel();
  finderLatLng = null;
  document.getElementById('finderStatus').textContent = window._isMobile() ? 'Долгое нажатие на карте — найти лучшую цену' : 'Alt+Click на карте — найти лучшую цену';
}}

// ── Обновление попапа ОТП при открытии ───────────────────────────────────────
function refreshOtpPopup(stationName, code) {{
  const detailEl = document.getElementById('otp-detail-' + code);
  const surchargeEl = document.getElementById('otp-surcharge-' + code);
  if (!detailEl || !surchargeEl) return;

  const detail = getOtpDetail(stationName);
  if (!detail) {{ surchargeEl.style.display='none'; return; }}

  const nalyv   = detail.nalyv   || 0;
  const storage = detail.storage || 0;
  const total   = nalyv + storage;

  if (total === 0) {{
    detailEl.innerHTML = '<span style="color:#aaa;">Надбавки не заданы — <a href="#" onclick="var W=(window.parent||window);W.openOtpModal();return false;" style="color:#f57c00;">настроить</a></span>';
  }} else {{
    detailEl.innerHTML = `
      Налив: <b>${{nalyv.toLocaleString()}} ₽/т</b><br>
      Хранение 5 дн.: <b>${{storage.toLocaleString()}} ₽/т</b><br>
      <span style="color:#e67e22;font-weight:700;">Итого надбавка: ${{total.toLocaleString()}} ₽/т</span>
    `;
  }}

  // Обновляем цены в таблице топлива — добавляем надбавку к каждой строке
  const table = document.getElementById('fuelTable-' + code);
  if (!table) return;
  table.querySelectorAll('td[data-base-price]').forEach(td => {{
    const base = parseFloat(td.getAttribute('data-base-price')) || 0;
    if (base === 0) return;
    const withOtp = base + total;
    // Сохраняем badge если есть (первый span с датой)
    const badge = td.querySelector('span') ? td.querySelector('span').outerHTML : '';
    if (total > 0) {{
      td.innerHTML = badge +
        `<span style="color:#007bff;font-weight:bold;">${{base.toLocaleString()}} ₽</span>` +
        `<span style="color:#e67e22;font-size:11px;"> +${{total.toLocaleString()}}</span><br>` +
        `<span style="color:#28a745;font-weight:bold;font-size:15px;">${{withOtp.toLocaleString()}} ₽</span>`;
    }} else {{
      td.innerHTML = badge +
        `<span style="color:#007bff;font-weight:bold;">${{base.toLocaleString()}} ₽</span>`;
    }}
  }});
}}

function findMap() {{
  for (let k in window) {{
    if (k.startsWith('map_') && window[k] instanceof L.Map) {{ mapInst = window[k]; return true; }}
  }}
  return false;
}}

// ── поиск ────────────────────────────────────────────────────────────────────
function searchStation() {{
  const q = (document.getElementById('searchInput').value||'').trim().toLowerCase();
  if (!q) return;
  const list = window.__STATIONS__ || [];
  let best = list.find(m=>(m._stationCode||'').toLowerCase()===q)
          || list.find(m=>(m._stationName||'').toLowerCase().includes(q))
          || list.find(m=>(m._stationCode||'').toLowerCase().includes(q));
  if (!best) {{ document.getElementById('calcStatus').innerHTML='Не найдено: <b>'+q+'</b>'; return; }}
  if (!mapInst.hasLayer(best)) best.addTo(mapInst);
  mapInst.setView(best.getLatLng(), Math.max(mapInst.getZoom(), 10));
  best.openPopup();
}}
document.addEventListener('keydown', e=>{{
  if (e.key==='Enter' && document.activeElement?.id==='searchInput') searchStation();
  if (e.key==='Escape') clearLogistics();
}});

// ── фильтры ──────────────────────────────────────────────────────────────────
function getActiveFilters() {{
  return {{
    comp: {{
      spimex:      document.getElementById('flt_spimex').checked,
      lukoil_spot: document.getElementById('flt_lukoil_spot').checked,
      lukoil_term: document.getElementById('flt_lukoil_term').checked,
      rosneft:     document.getElementById('flt_rosneft').checked,
      other:       document.getElementById('flt_other').checked,
    }},
    fuel: {{
      'Бензин': document.getElementById('flt_Benz').checked,
      'ДтЛ':   document.getElementById('flt_DtL').checked,
      'ДтЕ':   document.getElementById('flt_DtE').checked,
      'ДтЗ':   document.getElementById('flt_DtZ').checked,
      'ДтА':   document.getElementById('flt_DtA').checked,
      'СУГ':   document.getElementById('flt_SUG').checked,
    }}
  }};
}}
function companyPassesFilter(company, flt) {{
  const c=(company||'').toLowerCase();
  if (c==='spimex')        return flt.comp.spimex;
  if (c==='lukoil_spot')   return flt.comp.lukoil_spot;
  if (c==='lukoil_term')   return flt.comp.lukoil_term;
  if (c==='lukoil_merged') return flt.comp.lukoil_spot || flt.comp.lukoil_term;
  if (c==='rosneft')       return flt.comp.rosneft;
  return flt.comp.other;
}}
function markerPasses(mk, flt) {{
  if (!companyPassesFilter(mk._company, flt)) return false;
  const cats = mk._categories || [];
  if (cats.length===0) return true;
  return cats.some(cat => flt.fuel[cat]===true);
}}
function applyFilters() {{
  if (!mapInst) return;
  const flt = getActiveFilters();
  for (const mk of (window.__STATIONS__||[])) {{
    const ok = markerPasses(mk, flt);
    if (ok) {{ if (!mapInst.hasLayer(mk)) mk.addTo(mapInst); }}
    else    {{ if (mapInst.hasLayer(mk))  mapInst.removeLayer(mk); }}
  }}
}}

// ── панель ────────────────────────────────────────────────────────────────────
function minimizePanel() {{
  document.getElementById('uiPanel').style.display='none';
  document.getElementById('restoreBtn').style.display='flex';
}}
function restorePanel() {{
  document.getElementById('restoreBtn').style.display='none';
  document.getElementById('uiPanel').style.display='flex';
}}
(function() {{
  const panel=document.getElementById('uiPanel'), header=document.getElementById('uiHeader');
  let d=false,sx=0,sy=0,sl=0,st=0;
  header.addEventListener('mousedown',e=>{{
    d=true; const r=panel.getBoundingClientRect();
    sx=e.clientX;sy=e.clientY;sl=r.left;st=r.top;
    panel.style.cssText+=';left:'+sl+'px;top:'+st+'px;right:auto;bottom:auto;';
    e.preventDefault();
  }});
  window.addEventListener('mousemove',e=>{{if(!d)return;panel.style.left=(sl+(e.clientX-sx))+'px';panel.style.top=(st+(e.clientY-sy))+'px';}});
  window.addEventListener('mouseup',()=>d=false);
}})();

// ── waypoints UI ─────────────────────────────────────────────────────────────
function renderWaypointList() {{
  const el=document.getElementById('waypointList'); if(!el) return;
  if (!activeDelivery.code) {{ el.innerHTML=''; return; }}
  let html=`<div class="wp-item"><span class="wp-dot" style="background:#28a745;"></span><span>🏭 ${{activeDelivery.name}}</span></div>`;
  waypoints.forEach((wp,i)=>{{
    html+=`<div class="wp-item">
      <span class="wp-dot"></span>
      <span>Точка ${{i+1}}: ${{wp.lat.toFixed(4)}}, ${{wp.lon.toFixed(4)}}</span>
      <button class="wp-del" onclick="removeWaypoint(${{i}})">×</button>
    </div>`;
  }});
  el.innerHTML=html;
  document.getElementById('buildBtn').style.display=waypoints.length>0?'block':'none';
}}

function removeWaypoint(i) {{
  if (waypoints[i]?.marker) mapInst.removeLayer(waypoints[i].marker);
  waypoints.splice(i,1);
  renderWaypointList();
}}

function addWaypointMarker(latlng) {{
  const num=waypoints.length+1;
  const mk=L.circleMarker(latlng,{{radius:8,fillColor:'#007bff',color:'#fff',weight:2,fillOpacity:0.9}})
    .addTo(mapInst).bindTooltip('Точка '+num);
  waypoints.push({{lat:latlng.lat,lon:latlng.lng,marker:mk}});
  renderWaypointList();
  document.getElementById('calcStatus').innerHTML=
    `<b>Добавлена точка ${{num}}</b><br>Ещё кликайте или нажмите <b>«Построить маршрут»</b>.<br>Shift+Click — финиш.`;
}}

// ── логистика ─────────────────────────────────────────────────────────────────
function startDelivery(code, lat, lon, name) {{
  setTimeout(()=>{{
    _removeRouteControl();
    waypoints.forEach(w=>{{ if(w.marker) mapInst.removeLayer(w.marker); }});
    waypoints=[];
    activeDelivery={{code,lat,lon,name}};
    lastRoutePopupCode=null;
    collectingWpts=true;
    mapInst.getContainer().style.cursor='crosshair';
    var apb=document.getElementById('addPointBtn'); if(apb) apb.style.display='';
    renderWaypointList();
    document.getElementById('calcStatus').innerHTML=
      `<b>Отправитель:</b> ${{name}}<br><br>
       <span style="color:#b00020;font-weight:bold;">
         Кликайте точки маршрута.<br>
         На телефоне: нажмите кнопку <b>«+ Точка»</b> ниже.
       </span>`;
    const uc=document.getElementById('uiContent');
    if (uc.style.display==='none') uc.style.display='block';
  }},50);
}}

function _removeRouteControl() {{
  if (routingControl) {{ mapInst.removeControl(routingControl); routingControl=null; }}
}}

async function buildMultiRoute() {{
  if (!activeDelivery.code || waypoints.length===0) {{
    document.getElementById('calcStatus').innerHTML='Добавьте хотя бы одну точку маршрута.';
    return;
  }}
  collectingWpts=false;
  mapInst.getContainer().style.cursor='';
  var apb=document.getElementById('addPointBtn'); if(apb) apb.style.display='none';
  _removeRouteControl();

  const allPts=[L.latLng(activeDelivery.lat,activeDelivery.lon), ...waypoints.map(w=>L.latLng(w.lat,w.lon))];
  try {{
    await ensureRoutingMachine();
  }} catch (err) {{
    console.error('Routing machine load failed:', err);
    document.getElementById('calcStatus').innerHTML='Не удалось загрузить модуль логистики. Попробуйте ещё раз.';
    return;
  }}

  routingControl=L.Routing.control({{
    waypoints: allPts,
    routeWhileDragging: false,
    addWaypoints: false,
    draggableWaypoints: false,
    show: false,
    fitSelectedRoutes: true,
    lineOptions:{{styles:[{{color:'#007bff',weight:4,opacity:0.8,dashArray:'8,8'}}]}},
    router: L.Routing.osrmv1({{serviceUrl:'https://router.project-osrm.org/route/v1'}})
  }}).addTo(mapInst);

  routingControl.on('routesfound', function(e) {{
    const r=e.routes[0];
    const km      =(r.summary.totalDistance||0)/1000.0;
    const tariff  =getTariff();
    const tonnage =getTonnage();
    const tripCost=Math.round(km*tariff);
    const tonCost =Math.round(tripCost/tonnage);

    const resHtml=`
      <b>Маршрут:</b> ${{km.toFixed(1)}} км<br>
      <b>Тариф:</b> ${{tariff.toLocaleString()}} ₽/км &nbsp;·&nbsp; <b>Тоннаж:</b> ${{tonnage}} т<br>
      <b>Стоимость рейса:</b> ${{tripCost.toLocaleString()}} ₽<br>
      <b>Доставка / 1 т:</b> <span style="color:#28a745;font-size:13px;font-weight:bold;">${{tonCost.toLocaleString()}} ₽/т</span>`;

    document.getElementById('calcStatus').innerHTML='<b>Результат:</b><div class="result-box">'+resHtml+'</div>';

    const popDiv=document.getElementById('delivery-'+activeDelivery.code);
    if (popDiv) {{
      lastRoutePopupCode=activeDelivery.code;
      const safeNameAttr=(activeDelivery.name||'').replace(/"/g,'&quot;');
      popDiv.innerHTML=
        `<div class="result-box" style="margin:0;">${{resHtml}}</div>
         <button class="reset-delivery-btn"
           data-code="${{activeDelivery.code}}"
           data-lat="${{activeDelivery.lat}}"
           data-lon="${{activeDelivery.lon}}"
           data-name="${{safeNameAttr}}"
           style="margin-top:8px;background:#fff;color:#111;border:1px solid #111;
                  padding:5px 10px;border-radius:8px;cursor:pointer;font-size:11px;width:100%;">
           ↺ Рассчитать снова
         </button>`;
      const resetBtn = popDiv.querySelector('.reset-delivery-btn');
      if (resetBtn) resetBtn.addEventListener('click', function(ev) {{
        ev.stopPropagation();
        resetPopupDelivery(this.dataset.code, parseFloat(this.dataset.lat), parseFloat(this.dataset.lon), this.dataset.name);
      }});
    }}
  }});

  routingControl.on('routingerror', function() {{
    document.getElementById('calcStatus').innerHTML='Ошибка OSRM. Сервер недоступен.';
    mapInst.getContainer().style.cursor='';
  }});
}}

// Восстанавливает кнопку в попапе
function resetPopupDelivery(code, lat, lon, name) {{
  const popDiv=document.getElementById('delivery-'+code);
  if (popDiv) {{
    const safeNameAttr = (name||'').replace(/"/g,'&quot;');
    popDiv.innerHTML=`<button class="delivery-btn"
      data-code="${{code}}" data-lat="${{lat}}" data-lon="${{lon}}" data-name="${{safeNameAttr}}"
      style="background:#000;color:#fff;border:none;padding:6px 12px;font-size:11px;cursor:pointer;font-family:Arial;width:100%;">
      РАССЧИТАТЬ ЛОГИСТИКУ
    </button>`;
    // Навешиваем обработчик на восстановленную кнопку
    const btn = popDiv.querySelector('.delivery-btn');
    if (btn) btn.addEventListener('click', function(ev) {{
      ev.stopPropagation();
      startDelivery(this.dataset.code, parseFloat(this.dataset.lat), parseFloat(this.dataset.lon), this.dataset.name);
    }});
  }}
}}

// «Убрать маршрут» — линия удаляется, точки и отправитель сохраняются; кнопка в попапе сбрасывается
function clearRouteOnly() {{
  _removeRouteControl();
  if (lastRoutePopupCode) {{
    resetPopupDelivery(lastRoutePopupCode,
      activeDelivery.lat, activeDelivery.lon,
      (activeDelivery.name||'').replace(/'/g,"\\'"));
    lastRoutePopupCode=null;
  }}
  document.getElementById('calcStatus').innerHTML=
    'Маршрут удалён. Добавьте точки и нажмите «Построить маршрут».';
}}

// «Сбросить всё» — полный сброс
function clearLogistics() {{
  _removeRouteControl();
  waypoints.forEach(w=>{{ if(w.marker) mapInst.removeLayer(w.marker); }});
  waypoints=[];
  collectingWpts=false;
  if (lastRoutePopupCode) {{
    resetPopupDelivery(lastRoutePopupCode,
      activeDelivery.lat, activeDelivery.lon,
      (activeDelivery.name||'').replace(/'/g,"\\'"));
    lastRoutePopupCode=null;
  }}
  activeDelivery={{code:null,lat:null,lon:null,name:null}};
  if (mapInst) mapInst.getContainer().style.cursor='';
  renderWaypointList();
  document.getElementById('calcStatus').innerHTML='Сброшено. Выберите нефтебазу.';
}}

// ── обработчик кликов на карте ────────────────────────────────────────────────
// ── ОПРЕДЕЛЕНИЕ МОБИЛЬНОГО УСТРОЙСТВА ───────────────────────────────────────
window._isMobile = function() {{
  return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
}};

// ── ДОЛГОЕ НАЖАТИЕ (long press) — финдер или точка маршрута ──────────────────
(function() {{
  var _lpTimer = null;
  var _lpMoved = false;
  var _LP_MS   = 600;

  function onTouchStart(e) {{
    if (e.touches.length !== 1) return;
    _lpMoved = false;
    var touch = e.touches[0];
    var startX = touch.clientX, startY = touch.clientY;
    _lpTimer = setTimeout(function() {{
      if (_lpMoved) return;
      if (navigator.vibrate) navigator.vibrate(40);
      var map = window.mapInst;
      if (!map) return;
      var rect = map.getContainer().getBoundingClientRect();
      var point = L.point(startX - rect.left, startY - rect.top);
      var latlng = map.containerPointToLatLng(point);
      if (window.collectingWpts && window.activeDelivery && window.activeDelivery.code) {{
        addWaypointMarker(latlng);
      }} else {{
        openFinderAt(latlng);
      }}
    }}, _LP_MS);
  }}
  function onTouchMove() {{ _lpMoved = true; clearTimeout(_lpTimer); }}
  function onTouchEnd()  {{ clearTimeout(_lpTimer); }}

  function attachLongPress() {{
    var container = document.querySelector('.leaflet-container');
    if (!container) {{ setTimeout(attachLongPress, 300); return; }}
    container.addEventListener('touchstart', onTouchStart, {{passive: true}});
    container.addEventListener('touchmove',  onTouchMove,  {{passive: true}});
    container.addEventListener('touchend',   onTouchEnd,   {{passive: true}});
  }}
  attachLongPress();
}})();

// ── ОПРЕДЕЛЕНИЕ МОБИЛЬНОГО УСТРОЙСТВА ───────────────────────────────────────
window._isMobile = function() {{
  return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
}};


// ── ДОБАВИТЬ ТОЧКУ ПО ЦЕНТРУ КАРТЫ (кнопка для мобильных) ────────────────────
function addPointFromCenter() {{
  if (!window.collectingWpts || !window.activeDelivery || !window.activeDelivery.code) return;
  var center = window.mapInst.getCenter();
  addWaypointMarker(center);
}}

// Отслеживаем Alt отдельно — e.originalEvent.altKey ненадёжен в браузерах
// (Alt может перехватываться браузером или ОС до того как Leaflet получит событие)
let _altDown = false;
document.addEventListener('keydown', function(ev) {{
  if (ev.key === 'Alt') {{ _altDown = true; ev.preventDefault(); }}
}});
document.addEventListener('keyup', function(ev) {{
  if (ev.key === 'Alt') _altDown = false;
}});
// Сбрасываем флаг если окно теряет фокус
window.addEventListener('blur', function() {{ _altDown = false; }});

// ── МОБИЛЬНЫЙ ФИНДЕР — режим ожидания тапа ───────────────────────────────────
let _mobileFinderPending = false;  // ожидаем следующий тап для финдера

function activateMobileFinder() {{
  _mobileFinderPending = true;
  document.getElementById('finderStatus').textContent = 'Тапните на карте — где искать нефтебазу';
  document.getElementById('mobileFindBtn').textContent = '📍 Тапните на карте...';
  document.getElementById('mobileFindBtn').style.background = '#fd7e14';
  // Сворачиваем панель чтобы карта была видна
  var uc = document.getElementById('uiContent');
  if (uc && uc.style.display !== 'none') minimizePanel();
}}

function _resetMobileFindBtn() {{
  _mobileFinderPending = false;
  var btn = document.getElementById('mobileFindBtn');
  if (btn) {{
    btn.textContent = '🔍 Лучшая цена с доставкой';
    btn.style.background = '#007bff';
  }}
}}

function handleMapClick(e) {{
  // Мобильный финдер — ожидаем тап после нажатия кнопки
  if (_mobileFinderPending) {{
    _resetMobileFindBtn();
    openFinderAt(e.latlng);
    return;
  }}
  // Alt+Click — финдер (проверяем и флаг и originalEvent)
  const isAlt = _altDown || !!(e.originalEvent && e.originalEvent.altKey);
  if (isAlt) {{
    _altDown = false; // сбрасываем после использования
    openFinderAt(e.latlng);
    return;
  }}
  // Сбор точек маршрута
  if (!collectingWpts || !activeDelivery.code) return;
  const isShift = !!(e.originalEvent && e.originalEvent.shiftKey);
  addWaypointMarker(e.latlng);
  if (isShift || waypoints.length >= 10) {{
    buildMultiRoute();
  }}
}}

// ── ФИНДЕР — поиск с построением маршрутов по дорогам ───────────────────────
// Цвета маршрутов: 1-й (лучший) — зелёный, 2-й — оранжевый, 3-й — фиолетовый
const FINDER_COLORS = ['#28a745', '#fd7e14', '#6f42c1'];
const FINDER_MEDALS = ['🥇', '🥈', '🥉'];

let finderLatLng        = null;
let finderRouteControls = [];   // L.Routing.control объекты финдера
let finderDestMarker    = null; // маркер точки назначения
let finderActiveFuel    = null;
let finderCandidates    = [];   // топ-20 по прямой, отправляем запросы к OSRM
let finderOsrmResults   = [];   // {{candidate, roadKm, delivCost, totalTon}}
let finderPending       = 0;

function haversineDist(lat1,lon1,lat2,lon2) {{
  const R=6371, dLat=(lat2-lat1)*Math.PI/180, dLon=(lon2-lon1)*Math.PI/180;
  const a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}}

function openFinderAt(latlng) {{
  finderLatLng = latlng;
  clearFinderRoutes();

  // Ставим маркер точки назначения
  if (finderDestMarker) mapInst.removeLayer(finderDestMarker);
  finderDestMarker = L.circleMarker(latlng, {{
    radius:10, fillColor:'#ff4757', color:'#fff', weight:3, fillOpacity:1
  }}).addTo(mapInst).bindTooltip('📍 Точка назначения', {{permanent:false}});

  document.getElementById('finderCoords').innerHTML =
    '📍 <b>'+latlng.lat.toFixed(4)+'</b>, <b>'+latlng.lng.toFixed(4)+'</b>';

  // ── Детализированные виды топлива для кнопок финдера ──────────────────────
  // keywords — массив строк: совпадение ЛЮБОГО из них в имени топлива (OR логика)
  // Пустой массив keywords = принять любое топливо данной категории (cat)
  // ── Детализированные виды топлива для кнопок финдера ──────────────────────
  // keywords (OR): совпадение ЛЮБОГО ключевого слова в нижнем регистре названия топлива
  // Пустой keywords = принять любое топливо данной категории
  const FINDER_FUEL_SPECS = [
    // ── БЕНЗИН ──────────────────────────────────────────────────────────────
    {{ id:'Аи-100',     label:'АИ-100',                  cat:'Бензин', keywords:['аи-100','аи-100','100-к5'] }},
    {{ id:'Аи-98',      label:'АИ-98',                   cat:'Бензин', keywords:['аи-98','98-к5'] }},
    {{ id:'Аи-95',      label:'АИ-95 / Премиум-95',      cat:'Бензин', keywords:['аи-95','95-к5','премиум евро-95','премиум euro-95'] }},
    {{ id:'Аи-92',      label:'АИ-92 / Регуляр-92',      cat:'Бензин', keywords:['аи-92','92-к5','регуляр-92','регуляр 92'] }},
    {{ id:'БензОТП92',  label:'ОТП АИ-92',               cat:'Бензин', keywords:['отп бензин (аи-92','отп бензин(аи-92'] }},
    {{ id:'БензОТП95',  label:'ОТП АИ-95',               cat:'Бензин', keywords:['отп бензин (аи-95','отп бензин(аи-95'] }},
    {{ id:'Бензин',     label:'Бензин (любой)',           cat:'Бензин', keywords:[] }},

    // ── ДтЛ (летнее) ────────────────────────────────────────────────────────
    {{ id:'ДтЛсортС',   label:'ДтЛ сорт C (−5)',         cat:'ДтЛ',    keywords:['сорт c (дт-л','сорт с (дт-л','евро сорт c (дт-л','евро сорт с (дт-л','сорт c (дт-л-к5','сорт с (дт-л-к5','дт-л-к5) минус 5','euro-6) минус 5','дт евро, летнее, сорта c, эк. класса к5 марки дт-л-к5','дт евро, летнее, сорта с, эк. класса к5 марки дт-л-к5'] }},
    {{ id:'ДтЛсортD',   label:'ДтЛ сорт D (−10)',        cat:'ДтЛ',    keywords:['сорт d (дт-л','евро сорт d (дт-л','дт-л-к5) минус 10'] }},
    {{ id:'ДтЛОТПС',    label:'ОТП ДтЛ сорт C',         cat:'ДтЛ',    keywords:['отп дт евро сорт c (дт-л','отп дт евро сорт с (дт-л','отп дизельное топливо евро, летнее, сорт c','отп дизельное топливо евро, летнее, сорт с'] }},
    {{ id:'ДтЛОТПD',    label:'ОТП ДтЛ сорт D',         cat:'ДтЛ',    keywords:['отп дт евро сорт d (дт-л'] }},
    {{ id:'ДтЛ',        label:'ДтЛ (любой)',             cat:'ДтЛ',    keywords:[] }},

    // ── ДтЕ (межсезонное) ───────────────────────────────────────────────────
    {{ id:'ДтЕсортE',   label:'ДтЕ сорт E (−15)',        cat:'ДтЕ',    keywords:['сорт e (дт-е','сорт е (дт-е','евро сорт e (дт-е','евро сорт е (дт-е','дт-е-к5) минус 15'] }},
    {{ id:'ДтЕсортF',   label:'ДтЕ сорт F (−20)',        cat:'ДтЕ',    keywords:['сорт f (дт-е','евро сорт f (дт-е','дт-е-к5) минус 20'] }},
    {{ id:'ДтЕ',        label:'ДтЕ (любой)',             cat:'ДтЕ',    keywords:[] }},

    // ── ДтЗ (зимнее) ────────────────────────────────────────────────────────
    {{ id:'ДтЗм20',     label:'ДтЗ −20 (класс 0)',       cat:'ДтЗ',    keywords:['дт-з-к5) минус 20','евро класс 0 (дт-з','класс 0 (дт-з','отп дт евро класс 0 (дт-з'] }},
    {{ id:'ДтЗм26',     label:'ДтЗ −26 (класс 1)',       cat:'ДтЗ',    keywords:['дт-з-к5) минус 26','евро класс 1 (дт-з','класс 1 (дт-з'] }},
    {{ id:'ДтЗм32',     label:'ДтЗ −32 (класс 2)',       cat:'ДтЗ',    keywords:['дт-з-к5) минус 32','евро класс 2 (дт-з','класс 2 (дт-з'] }},
    {{ id:'ДтЗм35',     label:'ДтЗ −35 (класс 3)',       cat:'ДтЗ',    keywords:['дт-з-к5) минус 35','евро класс 3 (дт-з','класс 3 (дт-з'] }},
    {{ id:'ДтЗм38',     label:'ДтЗ −38 (класс 3)',       cat:'ДтЗ',    keywords:['дт-з-к5) минус 38','евро класс 3 (дт-з-к5) минус 38'] }},
    {{ id:'ДтЗ',        label:'ДтЗ (любой)',             cat:'ДтЗ',    keywords:[] }},

    // ── ДтА (арктическое) ───────────────────────────────────────────────────
    {{ id:'ДтАм44',     label:'ДтА −44 (вид 4)',         cat:'ДтА',    keywords:['минус 44','дт-а-к5) минус 44','вид 4 (дт-а','класс 4 (дт-а'] }},
    {{ id:'ДтАм45',     label:'ДтА −45',                 cat:'ДтА',    keywords:['дт-а-к5) минус 45'] }},
    {{ id:'ДтАм50',     label:'ДтА −50',                 cat:'ДтА',    keywords:['дт-а-к5) минус 50'] }},
    {{ id:'ДтАм52',     label:'ДтА −52 (вид 4)',         cat:'ДтА',    keywords:['минус 52','дт-а-к5) минус 52','вид 4 (дт-а-к5) минус 52'] }},
    {{ id:'ДтА',        label:'ДтА (любой)',             cat:'ДтА',    keywords:[] }},

    // ── СУГ ─────────────────────────────────────────────────────────────────
    {{ id:'СУГ',        label:'СУГ',                     cat:'СУГ',    keywords:[] }},
  ];
  // Сохраняем specs глобально для использования в runFinderWithRoutes
  window.__FINDER_SPECS__ = FINDER_FUEL_SPECS;

  // Проверяем, есть ли хотя бы одна нефтебаза в 300 км с нужным топливом
  // keywords: OR логика — достаточно совпадения ЛЮБОГО ключевого слова
  const searchRadius = getFinderRadius();
  document.getElementById('finderCoords').innerHTML =
    '📍 <b>'+latlng.lat.toFixed(4)+'</b>, <b>'+latlng.lng.toFixed(4)+'</b> · радиус <b>'+searchRadius+' км</b>';

  const availIds = new Set();
  for (const mk of (window.__STATIONS__||[])) {{
    const ll = mk.getLatLng();
    if (haversineDist(latlng.lat,latlng.lng,ll.lat,ll.lng) > searchRadius) continue;
    const sd = window.__STATION_DATA__ && window.__STATION_DATA__[mk._stationCode];
    if (!sd) continue;
    for (const spec of FINDER_FUEL_SPECS) {{
      if (availIds.has(spec.id)) continue;
      for (const f of (sd.fuels||[])) {{
        if (f.cat !== spec.cat || f.price == null) continue;
        const fn = (f.name||'').toLowerCase();
        // Пустые keywords = принять любое топливо категории
        if (spec.keywords.length === 0 || spec.keywords.some(kw => fn.includes(kw))) {{
          availIds.add(spec.id);
          break;
        }}
      }}
    }}
  }}

  const availSpecs = FINDER_FUEL_SPECS.filter(s => availIds.has(s.id));

  // Группируем по категориям для красивого отображения
  const groups = {{}};
  const groupOrder = ['Бензин','ДтЛ','ДтЕ','ДтЗ','ДтА','СУГ'];
  availSpecs.forEach(s => {{
    if (!groups[s.cat]) groups[s.cat] = [];
    groups[s.cat].push(s);
  }});

  document.getElementById('finderFuelSection').style.display = 'block';
  if (availSpecs.length === 0) {{
    document.getElementById('finderFuelBtns').innerHTML =
      '<span style="color:#888;">Нефтебаз в радиусе 300 км не найдено</span>';
  }} else {{
    let html = '';
    groupOrder.forEach(cat => {{
      if (!groups[cat]) return;
      html += `<div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.06em;margin:8px 0 4px;">${{cat}}</div>`;
      html += groups[cat].map(s =>
        `<button class="finder-fuel-btn" onclick="runFinderWithRoutes('${{s.id}}')" id="finderBtn_${{s.id}}">${{s.label}}</button>`
      ).join('');
    }});
    document.getElementById('finderFuelBtns').innerHTML = html;
  }}

  document.getElementById('finderResults').innerHTML = '';
  document.getElementById('finderLoader').style.display = 'none';
  document.getElementById('finderActions').style.display = 'none';

  // Открываем панель
  const fp = document.getElementById('finderPanel');
  fp.style.display = 'flex';

  document.getElementById('finderStatus').textContent = window._isMobile() ? 'Режим поиска активен (долгое нажатие)' : 'Режим поиска активен (Alt+Click)';
}}

function closeFinderPanel() {{
  document.getElementById('finderPanel').style.display = 'none';
  // Убираем маркер точки назначения при закрытии панели
  if (finderDestMarker) {{ mapInst.removeLayer(finderDestMarker); finderDestMarker=null; }}
  finderLatLng = null;
  document.getElementById('finderStatus').textContent = window._isMobile() ? 'Долгое нажатие на карте — найти лучшую цену' : 'Alt+Click на карте — найти лучшую цену';
}}

function clearFinderRoutes() {{
  finderRouteControls.forEach(rc => {{ try {{ mapInst.removeControl(rc); }} catch(e) {{}} }});
  finderRouteControls = [];
  finderOsrmResults   = [];
  finderPending       = 0;
  finderCandidates    = [];
  finderActiveFuel    = null;
  document.getElementById('finderResults').innerHTML = '';
  document.getElementById('finderActions').style.display = 'none';
  // Восстанавливаем полный список кнопок топлива
  document.getElementById('finderFuelChosen').style.display  = 'none';
  document.getElementById('finderFuelSection').style.display = 'block';
  document.querySelectorAll('.finder-fuel-btn').forEach(b=>b.classList.remove('active'));
}}

// Запрашиваем OSRM для одного кандидата (прямой HTTP-запрос к API)
async function osrmRouteKm(fromLat, fromLon, toLat, toLon) {{
  const url = `https://router.project-osrm.org/route/v1/driving/${{fromLon}},${{fromLat}};${{toLon}},${{toLat}}?overview=full&geometries=geojson`;
  try {{
    const resp = await fetch(url);
    const data = await resp.json();
    if (data.code !== 'Ok' || !data.routes || data.routes.length===0) return null;
    const route = data.routes[0];
    return {{
      km:       route.distance / 1000,
      geometry: route.geometry   // GeoJSON LineString
    }};
  }} catch(e) {{
    return null;
  }}
}}

async function runFinderWithRoutes(specId) {{
  if (!finderLatLng) return;

  // Находим спецификацию по id
  const spec = (window.__FINDER_SPECS__ || []).find(s => s.id === specId);
  if (!spec) return;

  // Сбрасываем предыдущий результат
  clearFinderRoutes();
  finderActiveFuel = specId;

  // Подсвечиваем кнопку и сворачиваем список
  document.querySelectorAll('.finder-fuel-btn').forEach(b=>b.classList.remove('active'));
  const btn = document.getElementById('finderBtn_'+specId);
  if (btn) btn.classList.add('active');
  collapseFinderFuel(spec.label);

  const tariff  = getTariff();
  const tonnage = getTonnage();
  const radius  = getFinderRadius();

  // 1. Собираем кандидатов (по прямой ≤ radius км), фильтруем по cat + keywords
  let candidates = [];
  for (const mk of (window.__STATIONS__||[])) {{
    const ll   = mk.getLatLng();
    const dist = haversineDist(finderLatLng.lat, finderLatLng.lng, ll.lat, ll.lng);
    if (dist > radius) continue;
    const sd = window.__STATION_DATA__ && window.__STATION_DATA__[mk._stationCode];
    if (!sd) continue;

    let bestFuel=null, bestPrice=Infinity;
    for (const f of (sd.fuels||[])) {{
      if (f.cat !== spec.cat) continue;
      if (f.price == null || f.price >= bestPrice) continue;
      // Проверяем ключевые слова (OR логика — любое совпадение)
      if (spec.keywords.length > 0) {{
        const fn = (f.name||'').toLowerCase();
        if (!spec.keywords.some(kw => fn.includes(kw))) continue;
      }}
      bestPrice = f.price;
      bestFuel  = f;
    }}
    if (!bestFuel) continue;

    // Индивидуальная надбавка ОТП для этой нефтебазы
    const otp       = getOtpSurcharge(sd.name);
    const basePrice = bestFuel.price + otp;

    const estDelivCost = Math.round(dist * tariff / tonnage);
    candidates.push({{
      name:         sd.name,
      lat:          ll.lat,
      lon:          ll.lng,
      fuelName:     bestFuel.name,
      fuelPrice:    bestFuel.price,
      otpSurcharge: otp,
      fuelDate:     bestFuel.date || '',
      straightKm:   dist,
      estTotal:     basePrice + estDelivCost
    }});
  }}

  if (candidates.length === 0) {{
    document.getElementById('finderLoader').style.display = 'none';
    document.getElementById('finderResults').innerHTML =
      '<p style="color:#888;margin-top:8px;">Нефтебаз с ценами «'+spec.label+'» в радиусе '+radius+' км не найдено</p>';
    return;
  }}

  // 2. Берём топ-10 по оценочной цене (снижаем нагрузку на OSRM)
  candidates.sort((a,b) => a.estTotal - b.estTotal);
  const top10 = candidates.slice(0, 10);

  // 3. Показываем лоадер
  const loader = document.getElementById('finderLoader');
  loader.style.display = 'block';
  document.getElementById('finderLoaderSub').textContent =
    'Запрашиваю маршруты для '+top10.length+' нефтебаз…';

  // 4. Параллельно запрашиваем OSRM для всех топ-10
  const osrmPromises = top10.map(c =>
    osrmRouteKm(c.lat, c.lon, finderLatLng.lat, finderLatLng.lng)
      .then(res => ({{ candidate: c, osrm: res }}))
  );

  const results = await Promise.all(osrmPromises);

  // 5. Рассчитываем финальные цены по реальному расстоянию + ОТП
  let scored = [];
  for (const {{candidate:c, osrm}} of results) {{
    const km      = osrm ? osrm.km : c.straightKm * 1.3;
    const deliv   = Math.round(km * tariff / tonnage);
    const total   = Math.round(c.fuelPrice + c.otpSurcharge + deliv);
    const geom    = osrm ? osrm.geometry : null;
    scored.push({{ ...c, roadKm:km, delivCost:deliv, totalTon:total, geometry:geom, isEstimate:!osrm }});
  }}

  // 6. Сортируем по финальной цене, берём топ-3
  scored.sort((a,b) => a.totalTon - b.totalTon);
  const top3 = scored.slice(0, 3);

  loader.style.display = 'none';

  // 7. Рисуем маршруты на карте (GeoJSON полилинии)
  top3.forEach((c, i) => {{
    const color = FINDER_COLORS[i];
    if (c.geometry) {{
      const routeLayer = L.geoJSON(c.geometry, {{
        style: {{ color, weight: i===0?6:4, opacity: i===0?0.9:0.65, dashArray: i===0?null:'10,6' }}
      }}).addTo(mapInst);
      finderRouteControls.push({{ _isGeoJSON:true, _layer:routeLayer, remove:()=>mapInst.removeLayer(routeLayer) }});
    }}

    // Маркер нефтебазы с номером
    const otpLine = c.otpSurcharge > 0
      ? `<br>ОТП (налив+хранение): <b>+${{c.otpSurcharge.toLocaleString()}} ₽/т</b>`
      : '';
    const nbMarker = L.circleMarker([c.lat, c.lon], {{
      radius:12, fillColor:color, color:'#fff', weight:3, fillOpacity:0.95
    }}).addTo(mapInst).bindPopup(
      `<div style="font-family:Arial;font-size:12px;min-width:200px;">
        <div style="font-weight:bold;font-size:14px;">${{FINDER_MEDALS[i]}} ${{c.name}}</div>
        <div style="color:#555;margin-top:4px;">${{c.fuelName}}
          ${{c.fuelDate?'<span style="background:#f1f3f5;border:1px solid #ddd;padding:1px 5px;border-radius:4px;font-size:10px;">'+c.fuelDate+'</span>':''}}
        </div>
        <div style="margin-top:8px;line-height:1.8;font-size:12px;">
          Расстояние: <b>${{c.roadKm.toFixed(1)}} км</b>${{c.isEstimate?' (~оценка)':''}}<br>
          Цена НБ: <b>${{c.fuelPrice.toLocaleString()}} ₽/т</b>
          ${{otpLine}}<br>
          Доставка: <b>+${{c.delivCost.toLocaleString()}} ₽/т</b><br>
          <span style="color:${{i===0?'#28a745':color}};font-weight:bold;font-size:14px;">
            Итого: ${{c.totalTon.toLocaleString()}} ₽/т
          </span>
        </div>
      </div>`
    );
    finderRouteControls.push({{ _isGeoJSON:true, _layer:nbMarker, remove:()=>mapInst.removeLayer(nbMarker) }});
  }});

  // Подгоняем вид карты
  try {{
    const pts = [[finderLatLng.lat, finderLatLng.lng], ...top3.map(c=>[c.lat, c.lon])];
    mapInst.fitBounds(L.latLngBounds(pts).pad(0.1));
  }} catch(e) {{}}

  // 8. Рендерим карточки результатов
  let html = `<div style="font-weight:700;font-size:12px;margin-bottom:8px;margin-top:4px;">
    Топ-3 · <b style="color:#333;">${{spec.label}}</b> · цена с доставкой:
  </div>`;

  top3.forEach((c,i) => {{
    const color = FINDER_COLORS[i];
    const db = c.fuelDate
      ? `<span style="background:#f1f3f5;border:1px solid #ddd;padding:1px 5px;border-radius:4px;font-size:10px;">${{c.fuelDate}}</span>`
      : '';
    const estBadge = c.isEstimate
      ? '<span style="background:#fff3cd;color:#856404;border:1px solid #ffc107;padding:1px 5px;border-radius:4px;font-size:9px;margin-left:4px;">~оценка</span>'
      : '';

    // Колонки: НБ | ОТП (если есть) | Доставка | Итого
    const hasOtp = c.otpSurcharge > 0;
    const gridCols = hasOtp ? '1fr 1fr 1fr 1fr' : '1fr 1fr 1fr';
    const otpCell = hasOtp ? `
      <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;padding:5px 6px;text-align:center;">
        <div style="color:#888;font-size:9px;">ОТП налив+хр.</div>
        <div style="font-weight:bold;color:#f57c00;">+${{c.otpSurcharge.toLocaleString()}}</div>
      </div>` : '';

    html += `
    <div class="finder-result-row${{i===0?' best':''}}" style="border-left-color:${{color}};">
      <div style="font-weight:bold;font-size:13px;">${{FINDER_MEDALS[i]}} ${{c.name}}</div>
      <div style="font-size:11px;color:#555;margin-top:3px;">
        ${{c.fuelName}} ${{db}} · <b>${{c.roadKm.toFixed(1)}} км</b> по дороге${{estBadge}}
      </div>
      <div style="margin-top:6px;display:grid;grid-template-columns:${{gridCols}};gap:4px;font-size:11px;">
        <div style="background:#fff;border:1px solid #eee;border-radius:8px;padding:5px 6px;text-align:center;">
          <div style="color:#888;font-size:10px;">Цена НБ</div>
          <div style="font-weight:bold;">${{c.fuelPrice.toLocaleString()}}</div>
        </div>
        ${{otpCell}}
        <div style="background:#fff;border:1px solid #eee;border-radius:8px;padding:5px 6px;text-align:center;">
          <div style="color:#888;font-size:10px;">Доставка</div>
          <div style="font-weight:bold;color:#e67e22;">+${{c.delivCost.toLocaleString()}}</div>
        </div>
        <div style="background:${{i===0?'#f0fff4':'#f8f9fa'}};border:2px solid ${{color}};border-radius:8px;padding:5px 6px;text-align:center;">
          <div style="color:#888;font-size:10px;">Итого/т</div>
          <div style="font-weight:bold;color:${{color}};font-size:13px;">${{c.totalTon.toLocaleString()}}</div>
        </div>
      </div>
    </div>`;
  }});

  html += `<div style="margin-top:8px;font-size:10px;color:#999;line-height:1.4;">
    Маршруты по дорогам OSRM. Тариф: ${{tariff.toLocaleString()}} ₽/км · Тоннаж: ${{tonnage}} т · Радиус: ${{radius}} км
  </div>`;

  document.getElementById('finderResults').innerHTML = html;
  document.getElementById('finderActions').style.display = 'flex';
}}

// ── инит ─────────────────────────────────────────────────────────────────────
setTimeout(()=>{{
  if (findMap()) {{
    // Инициализация OverlappingMarkerSpiderfier — spiderfy для совпадающих координат
    if (window.OverlappingMarkerSpiderfier) {{
      window.__OMS__ = new OverlappingMarkerSpiderfier(mapInst, {{
        keepSpiderfied: true,
        nearbyDistance: 20,
        legWeight: 1.5,
        circleSpiralSwitchover: 6,
      }});
      // Открываем попап по клику (OMS перехватывает нативный Leaflet click)
      window.__OMS__.addListener('click', function(mk) {{ mk.openPopup(); }});
      // Добавляем маркеры, зарегистрированные до инициализации OMS
      (window.__OMS_QUEUE__ || []).forEach(mk => window.__OMS__.addMarker(mk));
      window.__OMS_QUEUE__ = null;
    }}
    warmLoadOms();
    mapInst.on('click', handleMapClick);

    mapInst.on('popupopen', function(e) {{
      const el = e.popup.getElement();
      if (!el) return;
      // OTP block
      const otpDetail = el.querySelector('[id^="otp-detail-"]');
      if (otpDetail) {{
        const code = otpDetail.id.replace('otp-detail-', '');
        const titleEl = el.querySelector('[style*="font-size: 16px"]');
        const stationName = titleEl ? titleEl.textContent.trim() : '';
        refreshOtpPopup(stationName, code);
      }}
    }});

    setTimeout(applyFilters, 800);
    document.getElementById('uiContent').style.display='block';
    document.getElementById('finderStatus').textContent=window._isMobile() ? 'Долгое нажатие на карте — найти лучшую цену' : 'Alt+Click на карте — найти лучшую цену';
  }}
}}, 1500);
</script>
"""


# ──────────────────────────────────────────────────────────────────────────────
# МАРКЕРЫ
# ──────────────────────────────────────────────────────────────────────────────
LUKOIL_LOGO_B64 = "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"


TRANZIT_CITY_LOGO_B64 = "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"

ROSNEFT_LOGO_FILE = "rosneft_logo.png"


def _load_logo_b64(filepath):
    if not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return ""


ROSNEFT_LOGO_B64 = _load_logo_b64(ROSNEFT_LOGO_FILE)


def make_tc_icon():
    """????????? ?????? ??????? ????: ??????? ? ??????? ??????? 20px (??? ? ???????)."""
    return folium.DivIcon(
        html=f'''<div style="
            width:20px;height:20px;border-radius:50%;
            border:1.5px solid #0b5ea8;
            box-shadow:0 1px 4px rgba(0,0,0,.5);
            overflow:hidden;
            display:flex;align-items:center;justify-content:center;
            background:#fff;">
          <img src="data:image/jpeg;base64,{TRANZIT_CITY_LOGO_B64}"
               style="width:18px;height:18px;object-fit:contain;display:block;" />
        </div>''',
        icon_size=(20, 20),
        icon_anchor=(10, 10),
        popup_anchor=(0, -12),
    )

def make_lukoil_icon(dark=False):
    """Кастомная иконка Лукойл: логотип в круглом красном маркере 20px."""
    border = "#6b0000" if dark else "#a00020"
    return folium.DivIcon(
        html=f'''<div style="
            width:20px;height:20px;border-radius:50%;
            border:1.5px solid {border};
            box-shadow:0 1px 4px rgba(0,0,0,.5);
            overflow:hidden;
            display:flex;align-items:center;justify-content:center;
            background:#fff;">
          <img src="data:image/png;base64,{LUKOIL_LOGO_B64}"
               style="width:18px;height:18px;object-fit:contain;display:block;" />
        </div>''',
        icon_size=(20, 20),
        icon_anchor=(10, 10),
        popup_anchor=(0, -12),
    )


def make_rosneft_icon():
    """Кастомная иконка Роснефть: логотип в круглом маркере 20px."""
    if not ROSNEFT_LOGO_B64:
        return folium.Icon(color="black", icon="map-marker", prefix="fa")
    return folium.DivIcon(
        html=f'''<div style="
            width:20px;height:20px;border-radius:50%;
            border:1.5px solid #212529;
            box-shadow:0 1px 4px rgba(0,0,0,.5);
            overflow:hidden;
            display:flex;align-items:center;justify-content:center;
            background:#fff;">
          <img src="data:image/png;base64,{ROSNEFT_LOGO_B64}"
               style="width:18px;height:18px;object-fit:contain;display:block;" />
        </div>''',
        icon_size=(20, 20),
        icon_anchor=(10, 10),
        popup_anchor=(0, -12),
    )


def add_markers(map_obj, markers, group, company):
    is_lukoil = company in ("lukoil_spot", "lukoil_term")
    dark_red   = (company == "lukoil_term")

    for m_data in markers:
        popup_html = create_popup_html(m_data, company)

        if is_lukoil:
            icon = make_lukoil_icon(dark=dark_red)
        elif company == "rosneft":
            icon = make_rosneft_icon()
        elif company == "other":
            icon = make_tc_icon()
        else:
            icon = folium.Icon(color=m_data["color"], icon=m_data["icon"], prefix="fa")

        # НЕ передаём popup в folium.Marker — Folium оборачивает его в <iframe sandbox="">
        # что блокирует весь JS. Вместо этого bindPopup вызывается из js_meta ниже.
        marker = folium.Marker(
            [m_data["lat"], m_data["lon"]],
            icon=icon,
        )
        marker.add_to(group)

        m_name = marker.get_name()
        station_data_json = json.dumps({
            "name":  m_data.get("name", ""),
            "fuels": m_data.get("fuels", []),
        }, ensure_ascii=False)

        popup_html_escaped = popup_html.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

        js_meta = f"""
(function() {{
  var count = 0;
  var popupHtml = `{popup_html_escaped}`;
  function init() {{
    var mk = window['{m_name}'];
    if (mk) {{
      // Привязываем попап напрямую — без iframe sandbox
      mk.bindPopup(popupHtml, {{maxWidth: 400, className: 'custom-popup'}});
      mk._company     = {json.dumps('lukoil_merged' if m_data.get('_merged') else company)};
      mk._categories  = {json.dumps(m_data.get('categories', []), ensure_ascii=False)};
      mk._stationCode = {json.dumps(m_data.get('code'),           ensure_ascii=False)};
      mk._stationName = {json.dumps(m_data.get('name'),           ensure_ascii=False)};

      window.__STATIONS__ = window.__STATIONS__ || [];
      var exists = window.__STATIONS__.some(x => x._leaflet_id === mk._leaflet_id);
      if (!exists) window.__STATIONS__.push(mk);

      window.__STATION_DATA__ = window.__STATION_DATA__ || {{}};
      window.__STATION_DATA__[{json.dumps(m_data.get('code'), ensure_ascii=False)}] = {station_data_json};
      // OMS — регистрируем маркер для spiderfy при совпадении координат
      initOmsIfReady();
      if (window.__OMS__) {{ window.__OMS__.addMarker(mk); }}
      else {{ (window.__OMS_QUEUE__ = window.__OMS_QUEUE__ || []).push(mk); }}
    }} else if (count < 60) {{
      count++; setTimeout(init, 100);
    }}
  }}
  init();
}})();
"""
        map_obj.get_root().script.add_child(folium.Element(js_meta))


OTP_STAVKI_FILE = "stavkiOTP.txt"

OTP_STATION_KEYS = [
    'лпдс володарская', 'нс солнечногорская', 'нс нагорная', 'лпдс сокур',
    'лпдс невская', 'лпдс черкассы', 'лпдс никольское-1', 'нп брянск',
    'лпдс воронеж', 'лпдс белгород',
]

def load_otp_stavki():
    """Читает stavkiOTP.txt и возвращает dict {key: {nalyv, storage}}.
    Поддерживает два формата:
      - JSON (генерируется кнопкой «⬇ stavkiOTP.txt» в браузере)
      - Построчный: ключ | налив | хранение  # комментарий
    """
    result = {k: {"nalyv": 0, "storage": 0} for k in OTP_STATION_KEYS}
    if not os.path.exists(OTP_STAVKI_FILE):
        return result
    try:
        with open(OTP_STAVKI_FILE, encoding="utf-8") as f:
            raw = f.read().strip()

        # Пробуем JSON-формат
        if raw.startswith('{'):
            data = json.loads(raw)
            for k in OTP_STATION_KEYS:
                if k in data:
                    result[k]["nalyv"]   = float(data[k].get("nalyv",   0) or 0)
                    result[k]["storage"] = float(data[k].get("storage", 0) or 0)
        else:
            # Построчный формат: ключ | налив | хранение  # комментарий
            for line in raw.splitlines():
                line = line.split('#')[0].strip()   # убираем комментарии
                if '|' not in line:
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 3:
                    continue
                key = parts[0].lower()
                if key in result:
                    result[key]["nalyv"]   = float(parts[1] or 0)
                    result[key]["storage"] = float(parts[2] or 0)

        print(f"✅ Ставки ОТП загружены из {OTP_STAVKI_FILE}")
    except Exception as e:
        print(f"⚠️ Не удалось загрузить {OTP_STAVKI_FILE}: {e}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# ЗАГРУЗКА СПРАВОЧНИКА НЕФТЕБАЗ
# ──────────────────────────────────────────────────────────────────────────────
def load_stations_reference(csv_path=STATIONS_CSV):
    if not os.path.exists(csv_path):
        print(f"⚠️ Файл {csv_path} не найден.")
        return pd.DataFrame()

    df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)

    col_code = "code" if "code" in df.columns else df.columns[0]
    col_lat  = "lat"  if "lat"  in df.columns else df.columns[1]
    col_lon  = "lon"  if "lon"  in df.columns else df.columns[2]
    col_name = "name" if "name" in df.columns else df.columns[3]

    col_fuel = None
    for c in df.columns:
        cl = c.lower()
        if ("товар" in cl) or ("наименование" in cl) or ("fuel" in cl):
            col_fuel = c; break
    if col_fuel is None:
        col_fuel = df.columns[4] if len(df.columns) >= 5 else df.columns[-1]

    stations = pd.DataFrame()
    stations["code"]      = df[col_code].apply(normalize_code)
    stations["lat"]       = df[col_lat].apply(parse_coordinates)
    stations["lon"]       = df[col_lon].apply(parse_coordinates)
    stations["name"]      = df[col_name].astype(str)
    stations["fuel_type"] = df[col_fuel].astype(str)
    stations["category"]  = stations["fuel_type"].apply(get_fuel_category)
    return stations.dropna(subset=["lat", "lon"])


# ──────────────────────────────────────────────────────────────────────────────
# СПИМЕКС PDF
# Столбцы с конца:
#   [-3] — «лучшее предложение»  (best offer)
#   [-4] — «рыночная цена»       (market price)
# Логика:
#   • есть [-3] и есть [-4] → берём max([-3], [-4])
#   • есть [-3], нет  [-4]  → берём [-3]
#   • нет  [-3], есть [-4]  → НЕ показываем (пропускаем)
#   • нет обоих             → пропускаем
# ──────────────────────────────────────────────────────────────────────────────
def process_spimex_data(pdf_file, stations_df):
    if stations_df.empty: return []
    file_date = get_file_date_short(pdf_file)
    results = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table: continue
            for row in table:
                if not row or len(row) < 5: continue
                code        = normalize_code(row[0])
                price_best  = clean_price(row[-3])   # лучшее предложение
                price_mkt   = clean_price(row[-4])   # рыночная цена

                # Правило: показываем только если есть лучшее предложение
                if price_best is None:
                    continue

                # Если есть обе — берём максимум; если только best — берём best
                price = max(price_best, price_mkt) if price_mkt is not None else price_best

                if code:
                    match = stations_df[stations_df["code"] == code]
                    if not match.empty:
                        s = match.iloc[0]
                        actual_fuel_name = str(row[1]).strip() if len(row) > 1 and str(row[1]).strip() else s["fuel_type"]
                        cat = get_fuel_category(actual_fuel_name)
                        if cat is not None:
                            results.append({
                                "code": code, "name": s["name"], "lat": s["lat"], "lon": s["lon"],
                                "fuels": [{"name": actual_fuel_name, "price": price, "cat": cat, "date": file_date}]
                            })
    return results


# ──────────────────────────────────────────────────────────────────────────────
# АВТОЗАГРУЗКА ЛУКОЙЛ ПРАЙСА
# Парсит страницу auto.lukoil.ru, находит актуальную ссылку на XLSX,
# скачивает если файла с сегодняшней датой ещё нет.
# ──────────────────────────────────────────────────────────────────────────────
_LUKOIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}

def fetch_lukoil_xlsx(save_dir="."):
    """Скачивает актуальный прайс Лукойл со страницы оптовых цен.
    Возвращает путь к сохранённому файлу или None при ошибке.
    Если файл с датой публикации уже есть — возвращает его путь без скачивания.
    """
    # 1. Загружаем HTML страницы
    try:
        req  = Request(LUKOIL_PRICE_URL, headers=_LUKOIL_HEADERS)
        html = urlopen(req, timeout=15).read().decode("utf-8", errors="replace")
    except URLError as e:
        print(f"⚠️  Лукойл: не удалось загрузить страницу цен: {e}")
        return None

    # 2. Ищем ссылку на XLSX (/FileSystem/9/XXXXXX.xlsx...)
    xlsx_paths = re.findall(r'href=["\']?(/FileSystem/[^"\'>\s]+\.xlsx[^"\'>\s]*)', html, re.I)
    if not xlsx_paths:
        xlsx_paths = re.findall(r'(/FileSystem/\d+/\d+\.xlsx)', html, re.I)
    if not xlsx_paths:
        print("⚠️  Лукойл: ссылка на XLSX не найдена на странице")
        return None

    xlsx_url = LUKOIL_BASE_URL + xlsx_paths[0]
    if "dl=" not in xlsx_url:
        xlsx_url += ("&" if "?" in xlsx_url else "?") + "dl=1"

    # 3. Имя файла: сначала ищем дату рядом с конкретной ссылкой на XLSX, затем — резервные варианты.
    path_escaped = re.escape(xlsx_paths[0])
    date_m = re.search(
        rf'href=["\']{path_escaped}["\'][^>]*title=["\'][^"\']*?\bс\s+(\d{{2}})\.(\d{{2}})\.(\d{{4}})',
        html,
        re.I,
    )
    if not date_m:
        date_m = re.search(
            rf'title=["\'][^"\']*?\bс\s+(\d{{2}})\.(\d{{2}})\.(\d{{4}})[^"\']*["\'][^>]*href=["\']{path_escaped}',
            html,
            re.I,
        )
    if not date_m:
        idx = html.find(xlsx_paths[0])
        if idx >= 0:
            snippet = html[max(0, idx - 600): idx + 600]
            date_m = re.search(r'с\s+(\d{2})\.(\d{2})\.(\d{4})', snippet, re.I)
    if not date_m:
        date_m = re.search(r'Ликард\s+с\s+(\d{2})\.(\d{2})\.(\d{4})', html, re.I)
    if not date_m:
        date_m = re.search(r'с\s+(\d{2})\.(\d{2})\.(\d{4})', html, re.I)

    today_str = datetime.date.today().strftime("%Y%m%d")
    fname = (
        f"{LUKOIL_SPOT_PREFIX}_{date_m.group(3)}{date_m.group(2)}{date_m.group(1)}.xlsx"
        if date_m else
        f"{LUKOIL_SPOT_PREFIX}_{today_str}.xlsx"
    )
    save_path = os.path.join(save_dir, fname)
    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
        print(f"ℹ️  Лукойл: актуальный прайс уже есть — {os.path.basename(save_path)}")
        return save_path

    # 4. Скачиваем
    try:
        req2 = Request(xlsx_url, headers=_LUKOIL_HEADERS)
        data = urlopen(req2, timeout=30).read()
        with open(save_path, "wb") as f:
            f.write(data)
        print(f"✅ Лукойл: скачан прайс → {fname} ({len(data)//1024} КБ)")
        return save_path
    except URLError as e:
        print(f"⚠️  Лукойл: не удалось скачать файл {xlsx_url}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# СПРАВОЧНИК НЕФТЕБАЗ ЛУКОЙЛ
# stations_lukoil.csv: name (или station_name), lat, lon, code (опц.)
# Используется для сопоставления названий из прайса с координатами.
# ──────────────────────────────────────────────────────────────────────────────
def _norm_name(s):
    """Нормализует название нефтебазы для нечёткого сопоставления."""
    s = str(s).lower().strip()
    # ё → е (xlsx и csv могут использовать разные буквы)
    s = s.replace('ё', 'е')
    # убираем скобки и их содержимое, лишние пробелы
    s = re.sub(r'\(.*?\)', '', s)
    s = re.sub(r'[«»"\\\'.,]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    # Расширяем аббревиатуры: "нб " → "нефтебаза ", "нп " → "нефтепродукт "
    s = re.sub(r'\bнб\s+', 'нефтебаза ', s)
    s = re.sub(r'^нб$', 'нефтебаза', s)
    return s

def _name_score(a, b):
    """Оценка сходства двух нормализованных строк (0–1).
    Комбинирует вхождение подстроки и пересечение токенов.
    """
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # Пересечение слов
    ta = set(a.split())
    tb = set(b.split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    jaccard = inter / union
    # Бонус если одна строка содержит другую
    contains = 0.15 if (a in b or b in a) else 0.0
    return min(1.0, jaccard + contains)

_lukoil_stations_cache = None   # кэш CSV, чтобы не читать при каждом вызове

def load_lukoil_stations(csv_path=None):
    """Загружает stations_lukoil.csv → DataFrame с колонками:
    name_norm, name, lat, lon, code.
    Результат кэшируется.
    """
    global _lukoil_stations_cache
    if _lukoil_stations_cache is not None:
        return _lukoil_stations_cache

    if csv_path is None:
        csv_path = LUKOIL_STATIONS_CSV

    if not os.path.exists(csv_path):
        print(f"⚠️  Справочник {csv_path} не найден — координаты Лукойл из XLSX не будут проверены.")
        _lukoil_stations_cache = pd.DataFrame()
        return _lukoil_stations_cache

    df = None
    for enc in ("utf-8-sig", "utf-8", "cp1251", "windows-1251", "latin-1"):
        try:
            df = pd.read_csv(csv_path, encoding=enc, dtype=str)
            break
        except (UnicodeDecodeError, Exception):
            df = None
    if df is None:
        print(f"⚠️  Не удалось прочитать {csv_path} ни в одной кодировке.")
        _lukoil_stations_cache = pd.DataFrame()
        return _lukoil_stations_cache
    df.columns = [c.strip().lower() for c in df.columns]

    # Определяем колонки гибко
    def pick(candidates):
        for c in candidates:
            if c in df.columns: return c
        return None

    col_name = pick(["station_name", "name", "нефтебаза", "наименование"])
    col_lat  = pick(["lat", "latitude", "широта"])
    col_lon  = pick(["lon", "lng", "longitude", "долгота"])
    col_code = pick(["code", "код", "id"])

    # Fallback по позиции
    if col_name is None: col_name = df.columns[0]
    if col_lat  is None: col_lat  = df.columns[1]
    if col_lon  is None: col_lon  = df.columns[2]

    out = pd.DataFrame()
    out["name"]      = df[col_name].astype(str).str.strip()
    out["lat"]       = df[col_lat].apply(parse_coordinates)
    out["lon"]       = df[col_lon].apply(parse_coordinates)
    out["code"]      = df[col_code].apply(normalize_code) if col_code else out["name"].apply(
                        lambda x: "LUK_" + re.sub(r'\W+', '_', x.upper())[:20])
    out["name_norm"] = out["name"].apply(_norm_name)
    out = out.dropna(subset=["lat", "lon"])
    _lukoil_stations_cache = out
    print(f"✅ Справочник Лукойл: {len(out)} нефтебаз из {csv_path}")
    return out

def match_lukoil_station(xlsx_name, stations_df, threshold=0.40):
    """Находит лучшее совпадение в справочнике для названия из прайса.
    Возвращает строку DataFrame или None.
    """
    if stations_df.empty:
        return None
    norm = _norm_name(xlsx_name)
    best_score = -1
    best_row   = None
    for _, row in stations_df.iterrows():
        score = _name_score(norm, row["name_norm"])
        if score > best_score:
            best_score = score
            best_row   = row
    if best_score >= threshold:
        return best_row
    return None



# ──────────────────────────────────────────────────────────────────────────────
# ЛУКОЙЛ XLSX — разбор прайса
#
# Поддерживает два формата:
#   ДЛИННЫЙ (терм):  3 столбца без заголовков — Нефтебаза | Топливо | Цена
#   ШИРОКИЙ (спот):  строки = нефтебазы, столбцы = виды топлива
# Автоопределение: <=4 столбца и последний числовой -> длинный формат.
# ──────────────────────────────────────────────────────────────────────────────
def _detect_lukoil_format(df_raw):
    if len(df_raw.columns) <= 4:
        last = df_raw.iloc[:, -1].apply(clean_price)
        if last.notna().sum() / max(len(last), 1) >= 0.5:
            return "long"
    return "wide"


def _resolve_station(xlsx_name, stations_df, fallback_lat=None, fallback_lon=None, row_idx=0):
    if not stations_df.empty:
        m = match_lukoil_station(xlsx_name, stations_df)
        if m is not None:
            return str(m["name"]), m["lat"], m["lon"], str(m["code"])
        if fallback_lat is not None and fallback_lon is not None:
            return xlsx_name, fallback_lat, fallback_lon, "LUK_XLSX_" + str(row_idx)
        return None
    if fallback_lat is not None and fallback_lon is not None:
        return xlsx_name, fallback_lat, fallback_lon, "LUKOIL_" + str(row_idx)
    return None


def process_lukoil_xlsx(xlsx_file):
    if not os.path.exists(xlsx_file):
        return []
    file_date   = get_file_date_short(xlsx_file)
    stations_df = load_lukoil_stations()

    df_raw = pd.read_excel(xlsx_file, engine="openpyxl", dtype=str, header=None)
    df_raw = df_raw.dropna(how="all").reset_index(drop=True)

    fmt         = _detect_lukoil_format(df_raw)
    results     = []
    unmatched   = []
    matched_cnt = 0

    if fmt == "long":
        # ДЛИННЫЙ: Нефтебаза | Топливо | Цена
        print("   Лукойл: длинный формат (" + str(len(df_raw)) + " строк)")
        start_row = 1 if clean_price(df_raw.iloc[0, -1]) is None else 0
        from collections import defaultdict as _dd
        station_fuels = _dd(list)
        for i in range(start_row, len(df_raw)):
            row   = df_raw.iloc[i]
            sname = str(row.iloc[0]).strip()
            fname = str(row.iloc[1]).strip() if len(row) > 1 else ""
            price = clean_price(row.iloc[-1])
            if not sname or sname.lower() == "nan": continue
            if not fname or fname.lower() == "nan": continue
            if price is None: continue
            cat = get_fuel_category(fname)
            if cat is None: continue
            station_fuels[sname].append({"name": fname, "price": price, "cat": cat, "date": file_date})
        for sname, fuels in station_fuels.items():
            resolved = _resolve_station(sname, stations_df)
            if resolved is None:
                unmatched.append(sname)
                continue
            name, lat, lon, code = resolved
            matched_cnt += 1
            results.append({"code": code, "name": name, "lat": lat, "lon": lon, "fuels": fuels})

    else:
        # ШИРОКИЙ: строки = нефтебазы, столбцы = топливо
        header_row = 0
        for r in range(min(3, len(df_raw))):
            vals = [str(v) for v in df_raw.iloc[r] if str(v).strip() not in ("", "nan")]
            if len(vals) >= 2:
                header_row = r
                break
        df = pd.read_excel(xlsx_file, engine="openpyxl", dtype=str, header=header_row)
        df = df.dropna(how="all")
        print("   Лукойл: широкий формат (" + str(len(df)) + " строк)")

        def pick_col(candidates):
            for c in candidates:
                if c in df.columns: return c
            return None

        col_name   = pick_col(["Нефтебазы","Нефтебаза","station_name","name","Наименование"])
        col_region = pick_col(["Регион нефтебазы","Регион","region"])
        col_lat    = pick_col(["lat","широта","Latitude"])
        col_lon    = pick_col(["lon","lng","долгота","Longitude"])

        if col_name is None and len(df.columns) >= 1: col_name = df.columns[0]
        if col_lat  is None and len(df.columns) >= 3: col_lat  = df.columns[2]
        if col_lon  is None and len(df.columns) >= 4: col_lon  = df.columns[3]

        base_cols = {x for x in [col_region, col_name, col_lat, col_lon] if x}
        fuel_cols = [c for c in df.columns if c not in base_cols]

        for i, row in df.iterrows():
            xlsx_name = str(row.get(col_name,"")).strip() if col_name else ""
            if not xlsx_name or xlsx_name.lower() in ("nan",""): continue
            fuels = []
            for fc in fuel_cols:
                price = clean_price(row.get(fc))
                if price is None: continue
                cat = get_fuel_category(fc)
                if cat:
                    fuels.append({"name": fc, "price": price, "cat": cat, "date": file_date})
            if not fuels: continue
            fb_lat = parse_coordinates(row.get(col_lat)) if col_lat else None
            fb_lon = parse_coordinates(row.get(col_lon)) if col_lon else None
            resolved = _resolve_station(xlsx_name, stations_df, fb_lat, fb_lon, i+1)
            if resolved is None:
                unmatched.append(xlsx_name)
                continue
            name, lat, lon, code = resolved
            matched_cnt += 1
            results.append({"code": code, "name": name, "lat": lat, "lon": lon, "fuels": fuels})

    total = matched_cnt + len(unmatched)
    print("   Лукойл " + os.path.basename(xlsx_file) + ": совпадений " + str(matched_cnt) + "/" + str(total))
    if unmatched:
        print("   Не найдено (" + str(len(unmatched)) + "): " + ", ".join(unmatched))
    if results:
        names = ", ".join(r["name"] for r in results[:5])
        print("   Найдено (первые 5): " + names)
    return results


def process_lukoil_csv(csv_file):
    """Читает Лукойл Терм в CSV формате.
    Автоматически определяет разделитель (; или ,) и наличие заголовка.
    Формат строки: Нефтебаза;Топливо;Цена  или  Нефтебаза,Топливо,Цена
    """
    if not os.path.exists(csv_file):
        return []
    file_date   = get_file_date_short(csv_file)
    stations_df = load_lukoil_stations()
    results     = []
    unmatched   = []
    matched_cnt = 0

    from collections import defaultdict as _dd
    station_fuels = _dd(list)

    text = ""
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            with open(csv_file, encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            text = ""

    if not text:
        return []

    lines = text.splitlines()

    # Автоопределение разделителя по первой строке
    first = lines[0]
    sep = ";" if first.count(";") >= first.count(",") else ","
    print(f"   Лукойл CSV: разделитель {sep!r}, строк {len(lines)}")

    # Пропускаем строку заголовка если первая колонка не является названием нефтебазы
    # (нет цифр и есть слова типа "название", "нефтебаза", "топливо")
    skip_header = False
    first_parts = [p.strip().lower() for p in first.split(sep)]
    if first_parts and any(kw in first_parts[0] for kw in
                           ("название", "нефтебаз", "станц", "наименован")):
        skip_header = True
        print(f"   Лукойл CSV: пропускаем заголовок: {first.strip()!r}")

    reader = csv.reader(lines, delimiter=sep)
    for i, parts in enumerate(reader):
        if skip_header and i == 0:
            continue
        parts = [p.strip() for p in parts]
        if not parts or not any(parts):
            continue
        if len(parts) < 3:
            continue
        sname = parts[0]
        fname = parts[1]
        price = clean_price(parts[2])
        date_label = parts[3] if len(parts) >= 4 and parts[3] else file_date
        if not sname or not fname or price is None:
            continue
        cat = get_fuel_category(fname)
        if cat is None:
            continue
        station_fuels[sname].append({"name": fname, "price": price, "cat": cat, "date": date_label})

    for sname, fuels in station_fuels.items():
        resolved = _resolve_station(sname, stations_df)
        if resolved is None:
            unmatched.append(sname)
            continue
        name, lat, lon, code = resolved
        matched_cnt += 1
        results.append({"code": code, "name": name, "lat": lat, "lon": lon, "fuels": fuels})

    total = matched_cnt + len(unmatched)
    print(f"   Лукойл (CSV) {os.path.basename(csv_file)}: совпадений {matched_cnt}/{total}")
    if unmatched:
        print(f"   Не найдено ({len(unmatched)}): {', '.join(unmatched[:8])}")
    return results


def _download_vendor_asset(target_path, source_url):
    target = Path(target_path)
    if target.exists() and target.stat().st_size > 0:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(source_url, timeout=60)
        resp.raise_for_status()
        target.write_bytes(resp.content)
    except Exception as e:
        print(f"⚠️  Не удалось скачать asset {source_url}: {e}")


def ensure_local_vendor_assets(out_dir):
    for rel_path, source_url in VENDOR_ASSET_URLS.items():
        _download_vendor_asset(Path(out_dir) / rel_path, source_url)


def rewrite_html_vendor_links(html_path):
    try:
        text = Path(html_path).read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️  Не удалось прочитать {html_path}: {e}")
        return

    for remote_url, local_url in HTML_VENDOR_REWRITES.items():
        text = text.replace(remote_url, local_url)

    try:
        Path(html_path).write_text(text, encoding="utf-8")
    except Exception as e:
        print(f"⚠️  Не удалось обновить ссылки в {html_path}: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print("🚀 Сборка карты...")

    ref = load_stations_reference(STATIONS_CSV)
    m = folium.Map(location=[55.75, 37.62], zoom_start=5, tiles="cartodbpositron", zoom_control=False)
    add_map_layers(m)

    routing_css = ''
    routing_js  = ''
    m.get_root().header.add_child(folium.Element(routing_css))
    m.get_root().html.add_child(folium.Element(routing_js))
    oms_js = ''
    m.get_root().header.add_child(folium.Element(oms_js))

    # 1. СПИМЕКС
    date_str = "неизвестно"
    spimex_group = folium.FeatureGroup(name="Биржа", show=True)
    pdfs = glob.glob(os.path.join(DATA_FOLDER, "*.pdf"))
    if pdfs and not ref.empty:
        latest = sorted(pdfs)[-1]
        try:
            date_str = datetime.datetime.strptime(
                os.path.basename(latest).split("_")[1][:8], "%Y%m%d").strftime("%d.%m.%Y")
        except Exception:
            pass
        spimex_raw = process_spimex_data(latest, ref)
        if spimex_raw:
            spimex_data = aggregate_markers_by_coordinates(spimex_raw, precision=5, company="spimex")
            add_markers(m, spimex_data, spimex_group, "spimex")
            print(f"✅ СПИМЕКС: маркеров {len(spimex_data)} ({os.path.basename(latest)})")
    else:
        print(f"ℹ️ В {DATA_FOLDER} нет PDF или справочника — слой СПИМЕКС пустой.")
    spimex_group.add_to(m)

    # 2. ЛУКОЙЛ СПОТ — скачиваем актуальный прайс + предзагружаем справочник
    print("🔄 Проверяю актуальный прайс Лукойл...")
    fetch_lukoil_xlsx(save_dir=".")     # скачает если файла с сегодняшней датой нет
    load_lukoil_stations()              # предзагружаем CSV-справочник один раз

    spot_candidates = glob.glob("lukoil*spot*.xlsx") + glob.glob("lukoil*SPOT*.xlsx")
    if not spot_candidates:
        all_luk = glob.glob("lukoil*.xlsx")
        spot_candidates = [f for f in all_luk if "term" not in f.lower()]
    spot_files = pick_latest_files(spot_candidates, "Лукойл Спот")
    spot_raw = []
    for f in spot_files: spot_raw.extend(process_lukoil_xlsx(f))

    # 3. ЛУКОЙЛ ТЕРМ
    term_candidates = (
        glob.glob("lukoil*term*.xlsx") + glob.glob("lukoil*TERM*.xlsx") +
        glob.glob("lukoil*term*.csv")  + glob.glob("lukoil*TERM*.csv")
    )
    term_files = pick_latest_files(term_candidates, "Лукойл Терм")
    term_raw = []
    for f in term_files:
        if f.lower().endswith(".csv"):
            term_raw.extend(process_lukoil_csv(f))
        else:
            term_raw.extend(process_lukoil_xlsx(f))

    # Объединяем Спот и Терм — совпадающие нефтебазы → один маркер
    if spot_raw or term_raw:
        merged_raw = merge_lukoil_layers(spot_raw, term_raw)
        merged = [x for x in merged_raw if x.get("_merged")]
        spot_only = [x for x in merged_raw if not x.get("_merged") and
                     any(s["label"] == "Лукойл Спот" for s in x.get("sections", []))]
        term_only = [x for x in merged_raw if not x.get("_merged") and
                     any(s["label"] == "Лукойл Терм" for s in x.get("sections", []))]

        luk_group = folium.FeatureGroup(name="Лукойл Спот", show=True)
        all_spot = merged + spot_only
        if all_spot:
            sp_data = aggregate_markers_by_coordinates(all_spot, precision=5, company="lukoil_spot")
            add_markers(m, sp_data, luk_group, "lukoil_spot")
            print(f"✅ ЛУКОЙЛ СПОТ (вкл. объединённых {len(merged)}): маркеров {len(sp_data)}")
        luk_group.add_to(m)

        if term_only:
            tm_group = folium.FeatureGroup(name="Лукойл Терм", show=True)
            tm_data  = aggregate_markers_by_coordinates(term_only, precision=5, company="lukoil_term")
            add_markers(m, tm_data, tm_group, "lukoil_term")
            tm_group.add_to(m)
            print(f"✅ ЛУКОЙЛ ТЕРМ (только): маркеров {len(tm_data)}")

    # 4. РОСНЕФТЬ (из отдельных CSV)
    rosneft_raw = load_rosneft_prices()
    if rosneft_raw:
        rn_group = folium.FeatureGroup(name='ПАО "НК "Роснефть"', show=True)
        rn_data  = aggregate_markers_by_coordinates(rosneft_raw, precision=5, company="rosneft")
        add_markers(m, rn_data, rn_group, "rosneft")
        rn_group.add_to(m)
        print(f"✅ Роснефть: маркеров на карте {len(rn_data)}")

    # 5. TELEGRAM (цены от Юлии)
    tg_raw = load_telegram_prices()
    if tg_raw:
        tg_group = folium.FeatureGroup(name="Транзит Сити", show=True)
        tg_data  = aggregate_markers_by_coordinates(tg_raw, precision=4, company="other")
        add_markers(m, tg_data, tg_group, "other")
        tg_group.add_to(m)
        print(f"✅ Telegram: маркеров на карте {len(tg_data)}")

    # Собираем даты обновления по каждому поставщику для отображения в меню
    provider_dates = {
        "spimex":      date_str if date_str != "неизвестно" else "",
        "lukoil_spot": get_file_date_short(sorted(spot_files)[-1]) if spot_files else "",
        "lukoil_term": get_file_date_short(sorted(term_files)[-1]) if term_files else "",
        "rosneft":     get_rosneft_latest_date(),
        "other":       "",
    }
    # Дата Telegram берётся из JSON
    try:
        with open(TG_PRICES_JSON, encoding="utf-8") as _f:
            _tj = json.load(_f)
            _td = _tj.get("latest", {}).get("date", "")
            if _td:
                _parts = _td.split(".")
                provider_dates["other"] = _td
    except Exception:
        pass

    m.get_root().html.add_child(folium.Element(create_ui(provider_dates, load_otp_stavki())))

    out_dir  = Path(PUBLIC_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"
    if out_file.is_dir(): shutil.rmtree(out_file)
    m.save(str(out_file))
    ensure_local_vendor_assets(out_dir)
    rewrite_html_vendor_links(out_file)
    print(f"✅ Карта сохранена: {out_file}")


if __name__ == "__main__":
    main()
