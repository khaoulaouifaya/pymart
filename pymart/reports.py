"""Génération des rapports journaliers et mensuels.

Les rapports sont déterministes : les mêmes données et la même période
produisent exactement le même contenu (aucun horodatage variable).
"""

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def format_money(amount):
    """Formate un montant Decimal en euros avec 2 décimales."""
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f} €"


def _products_sold(orders):
    """Regroupe les quantités vendues et les montants par produit."""
    sales = {}
    for order in orders:
        if order.product_id not in sales:
            sales[order.product_id] = {"quantity": 0, "total": Decimal("0")}
        sales[order.product_id]["quantity"] += order.quantity
        sales[order.product_id]["total"] += order.total()
    return sales


def build_daily_report(products, orders, report_date):
    """Construit le rapport d'une journée donnée."""
    day_orders = sorted(
        [order for order in orders if order.order_date == report_date],
        key=lambda order: order.order_id,
    )

    if not day_orders:
        return (
            f"Rapport journalier - {report_date.isoformat()}\n"
            "\n"
            "Aucune commande ce jour."
        )

    sales = _products_sold(day_orders)
    total_quantity = sum(order.quantity for order in day_orders)
    total_amount = sum(
        (order.total() for order in day_orders), Decimal("0")
    )

    lines = [
        f"Rapport journalier - {report_date.isoformat()}",
        "",
        f"Nombre de commandes : {len(day_orders)}",
        f"Quantités vendues : {total_quantity}",
        f"Total des ventes : {format_money(total_amount)}",
        "",
        "Produits vendus :",
    ]
    for product_id in sorted(sales):
        product = products.get(product_id)
        name = product.name if product else "?"
        lines.append(
            f"  - {product_id} ({name}) : "
            f"{sales[product_id]['quantity']} vendu(s) pour "
            f"{format_money(sales[product_id]['total'])}"
        )
    return "\n".join(lines)


def build_monthly_report(products, orders, year, month):
    """Construit le rapport d'un mois donné."""
    month_orders = sorted(
        [
            order
            for order in orders
            if order.order_date.year == year and order.order_date.month == month
        ],
        key=lambda order: (order.order_date, order.order_id),
    )
    month_label = f"{year:04d}-{month:02d}"
    days_in_month = calendar.monthrange(year, month)[1]

    if not month_orders:
        return (
            f"Rapport mensuel - {month_label}\n"
            "\n"
            "Aucune commande ce mois."
        )

    sales = _products_sold(month_orders)
    total_amount = sum(
        (order.total() for order in month_orders), Decimal("0")
    )
    # Produits les plus vendus : tri par quantité décroissante.
    top_products = sorted(
        sales.items(),
        key=lambda item: (-item[1]["quantity"], item[0]),
    )

    lines = [
        f"Rapport mensuel - {month_label}",
        "",
        f"Mois concerné : {month_label} ({days_in_month} jours)",
        f"Nombre total de commandes : {len(month_orders)}",
        f"Chiffre d'affaires total : {format_money(total_amount)}",
        "",
        "Produits les plus vendus :",
    ]
    for product_id, info in top_products:
        product = products.get(product_id)
        name = product.name if product else "?"
        lines.append(f"  - {product_id} ({name}) : {info['quantity']} vendu(s)")

    lines.append("")
    lines.append("Résumé des ventes :")
    for product_id in sorted(sales):
        product = products.get(product_id)
        name = product.name if product else "?"
        lines.append(
            f"  - {product_id} ({name}) : {sales[product_id]['quantity']} "
            f"vendu(s) pour {format_money(sales[product_id]['total'])}"
        )
    return "\n".join(lines)


def write_report(content, output_dir, filename):
    """Écrit un rapport sur le disque et retourne son chemin."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    return path
