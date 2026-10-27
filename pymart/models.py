"""Modèles de données du projet PyMart.

Ce module contient les classes qui représentent les objets du magasin :
produits, produits numériques, clients et commandes.
"""

from decimal import Decimal, ROUND_HALF_UP

from .exceptions import InsufficientStockError


def to_decimal(value):
    """Convertit une valeur en Decimal (pour les montants financiers)."""
    return Decimal(str(value))


class Product:
    """Un produit vendu par le magasin."""

    def __init__(self, product_id, name, price, quantity):
        self.product_id = product_id
        self.name = name
        # Decimal évite les erreurs d'arrondi des nombres flottants.
        self.price = to_decimal(price)
        self.quantity = int(quantity)

    def get_price(self):
        """Retourne le prix unitaire du produit."""
        return self.price

    def is_available(self, quantity=1):
        """Indique si la quantité demandée est disponible en stock."""
        return self.quantity >= quantity

    def decrease_stock(self, quantity):
        """Retire la quantité commandée du stock."""
        if not self.is_available(quantity):
            raise InsufficientStockError(
                f"Stock insuffisant pour {self.product_id} : "
                f"{quantity} demandé, {self.quantity} disponible."
            )
        self.quantity -= quantity

    def display(self):
        """Retourne une description lisible du produit."""
        return (
            f"{self.product_id} - {self.name} - {self.price:.2f} €"
            f" - Stock : {self.quantity}"
        )

    def __str__(self):
        return self.display()


class DigitalProduct(Product):
    """Produit dématérialisé : son stock est illimité.

    Cette classe hérite de Product et redéfinit plusieurs méthodes pour
    démontrer le polymorphisme.
    """

    def is_available(self, quantity=1):
        # Un produit numérique est toujours disponible.
        return True

    def decrease_stock(self, quantity):
        # Pas de stock à décrémenter pour un produit numérique.
        pass

    def display(self):
        return (
            f"{self.product_id} - {self.name} - {self.price:.2f} €"
            f" - Produit dématérialisé (stock illimité)"
        )


class Customer:
    """Un client du magasin."""

    def __init__(self, customer_id, name, email):
        self.customer_id = customer_id
        self.name = name
        self.email = email

    def display(self):
        return f"{self.customer_id} - {self.name} - {self.email}"

    def __str__(self):
        return self.display()


class Order:
    """Une commande passée par un client."""

    def __init__(self, order_id, customer_id, product_id, quantity,
                 order_date, unit_price):
        self.order_id = order_id
        self.customer_id = customer_id
        self.product_id = product_id
        self.quantity = int(quantity)
        self.order_date = order_date  # objet datetime.date
        # Prix unitaire figé au moment de la commande (Decimal).
        self.unit_price = to_decimal(unit_price)

    def total(self):
        """Calcule le montant total de la commande."""
        return (self.unit_price * self.quantity).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def display(self):
        return (
            f"{self.order_id} - {self.order_date.isoformat()} - "
            f"Client {self.customer_id} - Produit {self.product_id} - "
            f"Quantité {self.quantity} - Total {self.total():.2f} €"
        )

    def __str__(self):
        return self.display()
