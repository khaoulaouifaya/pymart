"""Lecture et validation des fichiers d'importation.

Les fonctions parse_* lisent un fichier texte et retournent deux listes :
- items  : les objets valides ;
- errors : les messages d'erreur pour les lignes invalides.
Une ligne invalide ne bloque pas l'importation des autres lignes.
"""

import re
from datetime import date
from decimal import Decimal

from .models import Customer, DigitalProduct, Order, Product, to_decimal

PRODUCT_ID_PATTERN = re.compile(r"^P\d{3}$")
CUSTOMER_ID_PATTERN = re.compile(r"^C\d{3}$")
ORDER_ID_PATTERN = re.compile(r"^ORD\d{3}$")


def read_lines(file_path):
    """Générateur qui lit un fichier ligne par ligne.

    Utilité : pour de gros fichiers, on ne charge qu'une ligne à la fois en
    mémoire au lieu du fichier entier. On ignore les lignes vides et les
    commentaires (lignes qui commencent par #).
    """
    with open(file_path, "r", encoding="utf-8") as fichier:
        for line_number, raw_line in enumerate(fichier, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            yield line_number, line


def _split_columns(line):
    """Découpe une ligne avec le bon séparateur.

    Le séparateur normal est « ; ». Si la ligne utilise « | », on l'accepte
    aussi car la correction est possible sans ambiguïté.
    """
    if ";" in line:
        return [column.strip() for column in line.split(";")]
    if "|" in line:
        return [column.strip() for column in line.split("|")]
    return [line.strip()]


def _error(file_path, line_number, message):
    """Construit un message d'erreur avec le fichier et le numéro de ligne."""
    return f"{file_path}, ligne {line_number} : {message}"


def parse_products(file_path):
    """Lit et valide un fichier de produits.

    Format attendu : product_id;name;price;quantity
    Colonne optionnelle : type (physical ou digital).
    """
    items = []
    errors = []
    seen_ids = set()

    for line_number, line in read_lines(file_path):
        columns = _split_columns(line)
        # Normalisation : identifiant en majuscules.
        if columns:
            columns[0] = columns[0].upper()

        if len(columns) < 4:
            errors.append(_error(
                file_path, line_number,
                f"colonnes manquantes : attendu 4 ou 5, reçu {len(columns)}"
            ))
            continue
        if len(columns) > 5:
            errors.append(_error(
                file_path, line_number,
                f"trop de colonnes : attendu 4 ou 5, reçu {len(columns)}"
            ))
            continue

        product_id = columns[0]
        name = columns[1]
        price_text = columns[2]
        quantity_text = columns[3]
        product_type = columns[4].lower() if len(columns) == 5 else "physical"

        if not PRODUCT_ID_PATTERN.fullmatch(product_id):
            errors.append(_error(
                file_path, line_number,
                f"identifiant produit mal formé : {product_id}"
            ))
            continue

        if product_id in seen_ids:
            errors.append(_error(
                file_path, line_number,
                f"produit en double : {product_id}"
            ))
            continue

        try:
            price = to_decimal(price_text)
        except Exception:
            errors.append(_error(
                file_path, line_number,
                f"prix invalide : {price_text!r}"
            ))
            continue
        if price < 0:
            errors.append(_error(
                file_path, line_number,
                f"prix négatif : {price_text}"
            ))
            continue

        try:
            quantity = int(quantity_text)
        except ValueError:
            errors.append(_error(
                file_path, line_number,
                f"quantité invalide : {quantity_text!r}"
            ))
            continue
        if quantity < 0:
            errors.append(_error(
                file_path, line_number,
                f"quantité négative : {quantity_text}"
            ))
            continue

        if product_type not in ("physical", "digital"):
            errors.append(_error(
                file_path, line_number,
                f"type de produit inconnu : {product_type}"
            ))
            continue

        seen_ids.add(product_id)
        if product_type == "digital":
            items.append(DigitalProduct(product_id, name, price, quantity))
        else:
            items.append(Product(product_id, name, price, quantity))

    return items, errors


def parse_customers(file_path):
    """Lit et valide un fichier de clients.

    Format attendu : customer_id;name;email
    """
    items = []
    errors = []
    seen_ids = set()

    for line_number, line in read_lines(file_path):
        columns = _split_columns(line)
        if columns:
            columns[0] = columns[0].upper()

        if len(columns) != 3:
            errors.append(_error(
                file_path, line_number,
                f"format invalide : attendu 3 colonnes, reçu {len(columns)}"
            ))
            continue

        customer_id, name, email = columns

        if not CUSTOMER_ID_PATTERN.fullmatch(customer_id):
            errors.append(_error(
                file_path, line_number,
                f"identifiant client mal formé : {customer_id}"
            ))
            continue
        if customer_id in seen_ids:
            errors.append(_error(
                file_path, line_number,
                f"client en double : {customer_id}"
            ))
            continue
        if not name:
            errors.append(_error(file_path, line_number, "nom du client manquant"))
            continue
        # Vérification simple de l'e-mail (sans dépendance externe).
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append(_error(
                file_path, line_number,
                f"adresse e-mail invalide : {email}"
            ))
            continue

        seen_ids.add(customer_id)
        items.append(Customer(customer_id, name, email))

    return items, errors


def parse_orders(file_path):
    """Lit et valide un fichier de commandes.

    Format attendu : order_id;customer_id;product_id;quantity;order_date
    Le prix unitaire est mis à 0 ici : il sera renseigné par le service au
    moment de l'importation, à partir du produit correspondant.
    """
    items = []
    errors = []
    seen_ids = set()

    for line_number, line in read_lines(file_path):
        columns = _split_columns(line)
        # Normalisation : identifiants en majuscules.
        for index in (0, 1, 2):
            if index < len(columns):
                columns[index] = columns[index].upper()

        if len(columns) != 5:
            errors.append(_error(
                file_path, line_number,
                f"format invalide : attendu 5 colonnes, reçu {len(columns)}"
            ))
            continue

        order_id = columns[0]
        customer_id = columns[1]
        product_id = columns[2]
        quantity_text = columns[3]
        date_text = columns[4]

        if not ORDER_ID_PATTERN.fullmatch(order_id):
            errors.append(_error(
                file_path, line_number,
                f"identifiant de commande mal formé : {order_id}"
            ))
            continue
        if order_id in seen_ids:
            errors.append(_error(
                file_path, line_number,
                f"commande en double : {order_id}"
            ))
            continue
        if not CUSTOMER_ID_PATTERN.fullmatch(customer_id):
            errors.append(_error(
                file_path, line_number,
                f"identifiant client mal formé : {customer_id}"
            ))
            continue
        if not PRODUCT_ID_PATTERN.fullmatch(product_id):
            errors.append(_error(
                file_path, line_number,
                f"identifiant produit mal formé : {product_id}"
            ))
            continue

        try:
            quantity = int(quantity_text)
        except ValueError:
            errors.append(_error(
                file_path, line_number,
                f"quantité invalide : {quantity_text!r}"
            ))
            continue
        if quantity <= 0:
            errors.append(_error(
                file_path, line_number,
                f"quantité invalide (doit être positive) : {quantity_text}"
            ))
            continue

        try:
            order_date = date.fromisoformat(date_text)
        except ValueError:
            errors.append(_error(
                file_path, line_number,
                f"date invalide : {date_text}"
            ))
            continue

        seen_ids.add(order_id)
        items.append(Order(
            order_id, customer_id, product_id, quantity,
            order_date, Decimal("0")
        ))

    return items, errors
