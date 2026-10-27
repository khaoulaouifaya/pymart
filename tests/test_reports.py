"""Tests de la génération des rapports (reports.py)."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from pymart.models import Order, Product
from pymart.reports import (
    build_daily_report,
    build_monthly_report,
    write_report,
)


def make_products():
    return {
        "P001": Product("P001", "Laptop", "10.00", 10),
        "P002": Product("P002", "Mouse", "5.00", 10),
    }


def make_orders():
    return [
        Order("ORD001", "C001", "P001", 2, date(2026, 6, 30), "10.00"),
        Order("ORD002", "C001", "P002", 3, date(2026, 6, 30), "5.00"),
        Order("ORD003", "C001", "P001", 1, date(2026, 7, 1), "10.00"),
    ]


class TestDailyReport(unittest.TestCase):
    def test_content(self):
        report = build_daily_report(
            make_products(), make_orders(), date(2026, 6, 30)
        )
        self.assertIn("Rapport journalier - 2026-06-30", report)
        self.assertIn("Nombre de commandes : 2", report)
        self.assertIn("Quantités vendues : 5", report)
        self.assertIn("Total des ventes : 35.00 €", report)
        self.assertIn("P001", report)
        self.assertIn("P002", report)

    def test_deterministic(self):
        report1 = build_daily_report(
            make_products(), make_orders(), date(2026, 6, 30)
        )
        report2 = build_daily_report(
            make_products(), make_orders(), date(2026, 6, 30)
        )
        self.assertEqual(report1, report2)


class TestMonthlyReport(unittest.TestCase):
    def test_content(self):
        report = build_monthly_report(
            make_products(), make_orders(), 2026, 6
        )
        self.assertIn("Rapport mensuel - 2026-06", report)
        self.assertIn("Nombre total de commandes : 2", report)
        self.assertIn("Chiffre d'affaires total : 35.00 €", report)
        self.assertIn("Produits les plus vendus", report)

    def test_top_products_ordered(self):
        report = build_monthly_report(
            make_products(), make_orders(), 2026, 6
        )
        # P002 (3 unités) doit apparaître avant P001 (2 unités).
        self.assertLess(report.index("P002"), report.index("P001"))


class TestWriteReport(unittest.TestCase):
    def test_write_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_report(
                "contenu", Path(tmp) / "sous" / "reports", "rapport.txt"
            )
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding="utf-8"), "contenu")


if __name__ == "__main__":
    unittest.main()
