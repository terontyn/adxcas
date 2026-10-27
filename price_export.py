"""CSV adapter for Leaflet marker sections; independent of the OpenLayers schema."""
import csv
from pathlib import Path

FIELDS = ("company", "section", "station", "code", "lat", "lon", "fuel", "category", "price", "date")

def price_rows(markers, company):
    for marker in markers:
        sections = marker.get("sections") or [{"label": company, "fuels": marker.get("fuels", [])}]
        for section in sections:
            for fuel in section.get("fuels", []):
                yield dict(zip(FIELDS, (company, section.get("label", company), marker.get("name", ""), marker.get("code", ""), marker.get("lat"), marker.get("lon"), fuel.get("name", ""), fuel.get("cat", ""), fuel.get("price"), fuel.get("date", ""))))

def write_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    def safe(value):
        # Supplier-controlled strings must not become spreadsheet formulas.
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows({key: safe(row.get(key, "")) for key in FIELDS} for row in rows)
    temporary.replace(path)
    return path
