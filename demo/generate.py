"""Generate a real Folium/Leaflet UI from synthetic markers, without supplier fetches."""
import json
from pathlib import Path
import sys
import shutil
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import folium
import main as app
from price_export import price_rows, write_csv

def generate(out=None):
    root = Path(__file__).resolve().parents[1]
    out = Path(out or root / "public")
    out.mkdir(parents=True, exist_ok=True)
    markers = json.loads((root / "demo/stations.json").read_text(encoding="utf-8"))
    m = folium.Map(location=[56.82, 60.6], zoom_start=9, tiles="OpenStreetMap")
    rows = []
    for company in dict.fromkeys(x["company"] for x in markers):
        group = folium.FeatureGroup(name=company)
        normalized = app.aggregate_markers_by_coordinates([x for x in markers if x["company"] == company], company=company)
        app.add_markers(m, normalized, group, company, rows)
        group.add_to(m)
    m.get_root().html.add_child(folium.Element(app.create_ui({c: "DEMO" for c in ["spimex", "lukoil_spot", "lukoil_term", "rosneft", "other"]}, {})))
    m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:0;left:0;right:0;z-index:99999;background:#fff0b5;padding:10px;text-align:center;font:14px Arial">ДЕМОНСТРАЦИЯ · Все названия и цены вымышлены · Прайсы поставщиков не загружаются · Тайлы/OSRM требуют сети · <a href="prices.csv">CSV</a></div>'))
    m.save(str(out / "index.html"))
    app.rewrite_html_vendor_links(out / "index.html")
    vendor = root / "public/assets"
    if vendor.exists() and out.resolve() != (root / "public").resolve():
        shutil.copytree(vendor, out / "assets", dirs_exist_ok=True)
    write_csv(rows, out / "prices.csv")
    return out / "index.html"

if __name__ == "__main__":
    print(generate())
