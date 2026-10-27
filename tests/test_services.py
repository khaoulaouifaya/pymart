"""Tests des services : création de commandes et importations."""

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from pymart.exceptions import (
    InsufficientStockError,
    UnknownCustomerError,
    UnknownProductError,
)
from pymart.models import Customer, Product
from pymart.services import PyMartService


def write_temp(content):
    """Écrit un fichier temporaire et retourne son chemin."""
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return str(Path(tmp.name))


class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.service = PyMartService()
        self.service.products["P001"] = Product("P001", "Laptop", "999.99", 10)
        self.service.customers["C001"] = Customer(
            "C001", "Alice", "alice@example.com"
        )

    def test_create_order(self):
        order = self.service.create_order("c001", "p001", 2, date(2026, 6, 1))
        self.assertEqual(order.order_id, "ORD001")
        self.assertEqual(order.total(), Decimal("1999.98"))
        self.assertEqual(self.service.products["P001"].quantity, 8)

    def test_unknown_product(self):
        with self.assertRaises(UnknownProductError):
            self.service.create_order("C001", "P999", 1)

    def test_unknown_customer(self):
        with self.assertRaises(UnknownCustomerError):
            self.service.create_order("C999", "P001", 1)

    def test_insufficient_stock(self):
        with self.assertRaises(InsufficientStockError):
            self.service.create_order("C001", "P001", 11)

    def test_generated_ids_are_unique(self):
        self.service.create_order("C001", "P001", 1, date(2026, 6, 1))
        self.service.create_order("C001", "P001", 1, date(2026, 6, 1))
        self.assertEqual(len(self.service.orders), 2)
        self.assertEqual(self.service.products["P001"].quantity, 8)


class TestImportOrders(unittest.TestCase):
    def setUp(self):
        self.service = PyMartService()
        self.service.import_products(write_temp("P001;Laptop;10.00;5\n"))
        self.service.import_customers(write_temp("C001;Alice;a@example.com\n"))

    def test_import_orders_and_stock(self):
        path = write_temp("ORD001;C001;P001;2;2026-06-01\n")
        added, errors = self.service.import_orders(path)
        self.assertEqual(added, 1)
        self.assertEqual(errors, [])
        self.assertEqual(self.service.products["P001"].quantity, 3)

    def test_reimport_does_not_double_decrement(self):
        path = write_temp("ORD001;C001;P001;2;2026-06-01\n")
        self.service.import_orders(path)
        added, errors = self.service.import_orders(path)
        self.assertEqual(added, 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(self.service.products["P001"].quantity, 3)

    def test_unknown_references(self):
        path = write_temp(
            "ORD001;C999;P001;1;2026-06-01\n"
            "ORD002;C001;P999;1;2026-06-01\n"
        )
        added, errors = self.service.import_orders(path)
        self.assertEqual(added, 0)
        self.assertEqual(len(errors), 2)
        self.assertEqual(self.service.products["P001"].quantity, 5)


class TestImportDuplicates(unittest.TestCase):
    def test_duplicate_products_are_skipped(self):
        service = PyMartService()
        path = write_temp("P001;Laptop;10.00;5\n")
        service.import_products(path)
        added, errors = service.import_products(path)
        self.assertEqual(added, 0)
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
