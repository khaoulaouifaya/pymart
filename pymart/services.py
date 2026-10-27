"""Services : logique métier de l'application.

La classe PyMartService centralise les données du magasin (produits, clients,
commandes). La classe OrderService gère la création des commandes et le stock.
"""

import re
from datetime import date

from .exceptions import (
    DataValidationError,
    InsufficientStockError,
    UnknownCustomerError,
    UnknownProductError,
)
from .models import Order
from .parsers import parse_customers, parse_orders, parse_products


class OrderService:
    """Gère la création des commandes et le stock."""

    def __init__(self, products, customers, orders):
        # Dictionnaires partagés avec PyMartService.
        self.products = products
        self.customers = customers
        self.orders = orders

    def create_order(self, customer_id, product_id, quantity, order_date=None):
        """Crée une commande après toutes les vérifications."""
        customer_id = customer_id.upper()
        product_id = product_id.upper()

        if customer_id not in self.customers:
            raise UnknownCustomerError(f"Client inconnu : {customer_id}")
        if product_id not in self.products:
            raise UnknownProductError(f"Produit inconnu : {product_id}")

        if not isinstance(quantity, int) or quantity <= 0:
            raise DataValidationError("La quantité doit être un entier positif.")

        product = self.products[product_id]
        if not product.is_available(quantity):
            raise InsufficientStockError(
                f"Stock insuffisant pour {product_id} : "
                f"{quantity} demandé, {product.quantity} disponible."
            )

        # Le polymorphisme s'exerce ici : decrease_stock agit différemment
        # selon que le produit est physique ou numérique.
        product.decrease_stock(quantity)

        order_date = order_date or date.today()
        order = Order(
            order_id=self._next_order_id(),
            customer_id=customer_id,
            product_id=product_id,
            quantity=quantity,
            order_date=order_date,
            unit_price=product.get_price(),
        )
        self.orders[order.order_id] = order
        return order

    def _next_order_id(self):
        """Génère le prochain identifiant de commande sans collision."""
        max_number = 0
        for order_id in self.orders:
            match = re.fullmatch(r"ORD(\d+)", order_id)
            if match:
                max_number = max(max_number, int(match.group(1)))
        return f"ORD{max_number + 1:03d}"

    def list_orders(self):
        """Retourne les commandes triées par date puis par identifiant."""
        return sorted(
            self.orders.values(),
            key=lambda order: (order.order_date, order.order_id),
        )


class PyMartService:
    """Contient toutes les données et orchestre les importations."""

    def __init__(self):
        self.products = {}
        self.customers = {}
        self.orders = {}
        self.order_service = OrderService(
            self.products, self.customers, self.orders
        )

    # ------------------------------------------------------------------
    # Importations
    # ------------------------------------------------------------------

    def import_products(self, file_path):
        products, errors = parse_products(file_path)
        added = 0
        for product in products:
            if product.product_id in self.products:
                errors.append(
                    f"{file_path} : produit déjà importé : {product.product_id}"
                )
            else:
                self.products[product.product_id] = product
                added += 1
        return added, errors

    def import_customers(self, file_path):
        customers, errors = parse_customers(file_path)
        added = 0
        for customer in customers:
            if customer.customer_id in self.customers:
                errors.append(
                    f"{file_path} : client déjà importé : {customer.customer_id}"
                )
            else:
                self.customers[customer.customer_id] = customer
                added += 1
        return added, errors

    def import_orders(self, file_path):
        orders, errors = parse_orders(file_path)
        added = 0
        for order in orders:
            # Évite de traiter deux fois la même commande (et donc de
            # décrémenter deux fois le stock).
            if order.order_id in self.orders:
                errors.append(
                    f"{file_path} : commande déjà importée : {order.order_id}"
                )
                continue

            if order.product_id not in self.products:
                errors.append(
                    f"{file_path} : produit inconnu pour la commande "
                    f"{order.order_id} : {order.product_id}"
                )
                continue
            if order.customer_id not in self.customers:
                errors.append(
                    f"{file_path} : client inconnu pour la commande "
                    f"{order.order_id} : {order.customer_id}"
                )
                continue

            product = self.products[order.product_id]
            if not product.is_available(order.quantity):
                errors.append(
                    f"{file_path} : stock insuffisant pour la commande "
                    f"{order.order_id} ({product.product_id}, "
                    f"{order.quantity} demandé, {product.quantity} disponible)"
                )
                continue

            product.decrease_stock(order.quantity)
            order.unit_price = product.get_price()
            self.orders[order.order_id] = order
            added += 1
        return added, errors

    # ------------------------------------------------------------------
    # Commandes
    # ------------------------------------------------------------------

    def create_order(self, customer_id, product_id, quantity, order_date=None):
        return self.order_service.create_order(
            customer_id, product_id, quantity, order_date
        )

    def list_orders(self):
        return self.order_service.list_orders()
