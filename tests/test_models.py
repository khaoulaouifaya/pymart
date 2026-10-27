"""Tests des modèles de données (models.py)."""

import unittest
from datetime import date
from decimal import Decimal

from pymart.models import Customer, DigitalProduct, Order, Product


class TestProduct(unittest.TestCase):
    def test_creation(self):
        product = Product("P001", "Laptop", "999.99", 10)
        self.assertEqual(product.product_id, "P001")
        self.assertEqual(product.name, "Laptop")
        self.assertEqual(product.get_price(), Decimal("999.99"))
        self.assertEqual(product.quantity, 10)

    def test_decimal_avoid_float_errors(self):
        product = Product("P001", "Laptop", "0.1", 10)
        # 0.1 + 0.1 doit donner exactement 0.2 et non 0.30000000000000004.
        self.assertEqual(
            product.get_price() + product.get_price(), Decimal("0.2")
        )

    def test_stock_management(self):
        product = Product("P001", "Laptop", "10.00", 3)
        self.assertTrue(product.is_available(2))
        product.decrease_stock(2)
        self.assertEqual(product.quantity, 1)
        self.assertFalse(product.is_available(2))


class TestDigitalProduct(unittest.TestCase):
    def test_inheritance(self):
        digital = DigitalProduct("P006", "Ebook", "24.99", 0)
        self.assertIsInstance(digital, Product)

    def test_polymorphism(self):
        physical = Product("P001", "Laptop", "10.00", 1)
        digital = DigitalProduct("P006", "Ebook", "24.99", 0)
        # Même appel, comportement différent : c'est le polymorphisme.
        self.assertFalse(physical.is_available(5))
        self.assertTrue(digital.is_available(1000))
        physical.decrease_stock(1)
        digital.decrease_stock(1000)  # ne change rien
        self.assertEqual(physical.quantity, 0)
        self.assertEqual(digital.quantity, 0)

    def test_display_differs(self):
        physical = Product("P001", "Laptop", "10.00", 1)
        digital = DigitalProduct("P006", "Ebook", "24.99", 0)
        self.assertNotEqual(physical.display(), digital.display())
        self.assertIn("illimité", digital.display())


class TestCustomer(unittest.TestCase):
    def test_creation(self):
        customer = Customer("C001", "Alice", "alice@example.com")
        self.assertEqual(customer.customer_id, "C001")
        self.assertEqual(customer.name, "Alice")
        self.assertEqual(customer.email, "alice@example.com")


class TestOrder(unittest.TestCase):
    def test_total(self):
        order = Order("ORD001", "C001", "P001", 2, date(2026, 6, 1), "19.99")
        self.assertEqual(order.total(), Decimal("39.98"))

    def test_total_with_decimal(self):
        order = Order("ORD001", "C001", "P001", 3, date(2026, 6, 1), "0.10")
        self.assertEqual(order.total(), Decimal("0.30"))


if __name__ == "__main__":
    unittest.main()
