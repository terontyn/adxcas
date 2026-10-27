import csv
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from price_export import price_rows, write_csv
from run import next_run

class ExportTests(unittest.TestCase):
    def test_merged_sections_keep_both_prices(self):
        marker = {"name": "Demo", "sections": [{"label": "Spot", "fuels": [{"name": "diesel", "price": 10}]}, {"label": "Term", "fuels": [{"name": "diesel", "price": 12}]}]}
        rows = list(price_rows([marker], "lukoil"))
        self.assertEqual([r["section"] for r in rows], ["Spot", "Term"])
        self.assertEqual([r["price"] for r in rows], [10, 12])
    def test_csv_escapes_supplier_formula_and_keeps_numeric_price(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_csv([{"station": "=1+1", "price": 15.5}], Path(d) / "prices.csv")
            with path.open(encoding="utf-8-sig") as source:
                row = next(csv.DictReader(source, delimiter=";"))
            self.assertEqual(row["station"], "'=1+1")
            self.assertEqual(row["price"], "15.5")
    def test_schedule_moves_to_next_day(self):
        now = datetime(2026, 10, 27, 14, 5, tzinfo=timezone.utc)
        self.assertEqual(next_run(now, "14:05").day, 28)
        self.assertEqual(next_run(now, "15:05").day, 27)
