"""Tests des fonctions de lecture et de validation (parsers.py)."""

import tempfile
import unittest
from pathlib import Path

from pymart.models import DigitalProduct
from pymart.parsers import (
    parse_customers,
    parse_orders,
    parse_products,
    read_lines,
)


def write_temp(content):
    """Écrit un fichier temporaire et retourne son chemin."""
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return str(Path(tmp.name))


class TestReadLines(unittest.TestCase):
    def test_generator_skips_empty_and_comments(self):
        path = write_temp("# commentaire\n\nP001;Laptop;10.00;5\n")
        lines = list(read_lines(path))
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], (3, "P001;Laptop;10.00;5"))


class TestParseProducts(unittest.TestCase):
    def test_valid_file(self):
        path = write_temp(
            "P001;Laptop;999.99;10\n"
            "P002;Ebook;24.99;0;digital\n"
        )
        items, errors = parse_products(path)
        self.assertEqual(len(items), 2)
        self.assertEqual(errors, [])
        self.assertIsInstance(items[1], DigitalProduct)

    def test_invalid_lines_are_reported(self):
        path = write_temp(
            "P001;Bon produit;10.00;5\n"
            "P001;Doublon;10.00;5\n"      # doublon
            "P2;ID mal formé;10.00;5\n"   # identifiant mal formé
            "P010;Prix négatif;-5;5\n"    # prix négatif
            "P011;Prix invalide;abc;5\n"  # prix invalide
            "P012;Quantité négative;10.00;-1\n"
        )
        items, errors = parse_products(path)
        self.assertEqual(len(items), 1)
        self.assertEqual(len(errors), 5)

    def test_wrong_separator_is_fixed(self):
        path = write_temp("P001|Laptop|10.00|5|physical\n")
        items, errors = parse_products(path)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].product_id, "P001")

    def test_id_case_is_normalized(self):
        path = write_temp("p001;Laptop;10.00;5\n")
        items, errors = parse_products(path)
        self.assertEqual(items[0].product_id, "P001")


class TestParseCustomers(unittest.TestCase):
    def test_valid_and_invalid(self):
        path = write_temp(
            "c001;Alice;alice@example.com\n"
            "C001;Doublon;a@example.com\n"
            "C2;ID mal formé;x@example.com\n"
            "C100;E-mail invalide;pas-un-email\n"
        )
        items, errors = parse_customers(path)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].customer_id, "C001")
        self.assertEqual(len(errors), 3)


class TestParseOrders(unittest.TestCase):
    def test_valid_and_invalid(self):
        path = write_temp(
            "ord001;c001;p001;2;2026-06-01\n"
            "ORD001;C001;P001;1;2026-06-02\n"   # doublon
            "ORD002;C001;P001;0;2026-06-01\n"   # quantité nulle
            "ORD003;C001;P001;1;2026-13-01\n"   # date invalide
        )
        items, errors = parse_orders(path)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].order_id, "ORD001")
        self.assertEqual(len(errors), 3)


if __name__ == "__main__":
    unittest.main()
