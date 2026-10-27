"""Sauvegarde et chargement des données sur le disque.

On utilise un fichier JSON local (sans base de données). Les fichiers sources
fournis par l'utilisateur (products.txt, customers.txt, orders.txt) ne sont
jamais modifiés : l'état du magasin est écrit dans un fichier séparé.
"""

import json
from datetime import date
from pathlib import Path

from .models import Customer, DigitalProduct, Order, Product

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STORAGE_FILE = DATA_DIR / "pymart_store.json"


def save_state(file_path, products, customers, orders):
    """Écrit l'état complet du magasin dans un fichier JSON."""
    data = {
        "products": [
            {
                "product_id": product.product_id,
                "name": product.name,
                "price": str(product.price),
                "quantity": product.quantity,
                "type": (
                    "digital"
                    if isinstance(product, DigitalProduct)
                    else "physical"
                ),
            }
            for product in sorted(
                products.values(), key=lambda product: product.product_id
            )
        ],
        "customers": [
            {
                "customer_id": customer.customer_id,
                "name": customer.name,
                "email": customer.email,
            }
            for customer in sorted(
                customers.values(), key=lambda customer: customer.customer_id
            )
        ],
        "orders": [
            {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "order_date": order.order_date.isoformat(),
                "unit_price": str(order.unit_price),
            }
            for order in sorted(
                orders.values(), key=lambda order: order.order_id
            )
        ],
    }
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as fichier:
        json.dump(data, fichier, ensure_ascii=False, indent=2)


def load_state(file_path):
    """Reconstruit l'état du magasin depuis un fichier JSON.

    Retourne trois dictionnaires : products, customers, orders.
    Si le fichier n'existe pas, on retourne des dictionnaires vides.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return {}, {}, {}

    with open(file_path, "r", encoding="utf-8") as fichier:
        data = json.load(fichier)

    products = {}
    for item in data.get("products", []):
        if item.get("type") == "digital":
            product = DigitalProduct(
                item["product_id"], item["name"], item["price"], item["quantity"]
            )
        else:
            product = Product(
                item["product_id"], item["name"], item["price"], item["quantity"]
            )
        products[product.product_id] = product

    customers = {}
    for item in data.get("customers", []):
        customer = Customer(item["customer_id"], item["name"], item["email"])
        customers[customer.customer_id] = customer

    orders = {}
    for item in data.get("orders", []):
        order = Order(
            order_id=item["order_id"],
            customer_id=item["customer_id"],
            product_id=item["product_id"],
            quantity=item["quantity"],
            order_date=date.fromisoformat(item["order_date"]),
            unit_price=item["unit_price"],
        )
        orders[order.order_id] = order

    return products, customers, orders
