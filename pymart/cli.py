"""Interface en ligne de commande de PyMart (module argparse)."""

import argparse
import sys
import time
from datetime import date

from .exceptions import PyMartError
from .reports import build_daily_report, build_monthly_report, write_report
from .services import PyMartService
from .storage import DATA_DIR, STORAGE_FILE, load_state, save_state

REPORTS_DIR = DATA_DIR / "reports"


def _load_service():
    """Charge l'état sauvegardé dans un service PyMartService."""
    service = PyMartService()
    products, customers, orders = load_state(STORAGE_FILE)
    # On remplit les dictionnaires en place (sans les remplacer) afin que
    # OrderService garde ses références vers les bons dictionnaires.
    service.products.clear()
    service.products.update(products)
    service.customers.clear()
    service.customers.update(customers)
    service.orders.clear()
    service.orders.update(orders)
    return service


def _save_service(service):
    """Sauvegarde l'état du service sur le disque."""
    save_state(
        STORAGE_FILE, service.products, service.customers, service.orders
    )


def _print_errors(errors):
    for message in errors:
        print(f"  [ERREUR] {message}")


def cmd_import(args):
    service = _load_service()
    total_added = 0
    all_errors = []

    if args.products:
        started = time.time()
        added, errors = service.import_products(args.products)
        total_added += added
        all_errors.extend(errors)
        print(f"Produits importés : {added}")
        print(f"  (durée : {time.time() - started:.3f} s)")

    if args.customers:
        added, errors = service.import_customers(args.customers)
        total_added += added
        all_errors.extend(errors)
        print(f"Clients importés : {added}")

    if args.orders:
        added, errors = service.import_orders(args.orders)
        total_added += added
        all_errors.extend(errors)
        print(f"Commandes importées : {added}")

    if all_errors:
        print(f"\n{len(all_errors)} ligne(s) ignorée(s) :")
        _print_errors(all_errors)

    _save_service(service)
    print(f"\nTotal des enregistrements ajoutés : {total_added}")
    print(f"Données sauvegardées dans : {STORAGE_FILE}")
    return 0


def cmd_order_create(args):
    service = _load_service()
    try:
        order = service.create_order(args.customer, args.product, args.quantity)
    except PyMartError as error:
        print(f"Erreur : {error}")
        return 1
    _save_service(service)
    print("Commande créée avec succès :")
    print(f"  {order.display()}")
    return 0


def cmd_order_list(args):
    service = _load_service()
    orders = service.list_orders()
    if not orders:
        print("Aucune commande enregistrée.")
        return 0
    print(f"{len(orders)} commande(s) :")
    for order in orders:
        print(f"  {order.display()}")
    return 0


def cmd_report(args):
    service = _load_service()
    orders = service.list_orders()
    out_dir = args.out if args.out else REPORTS_DIR

    if args.type == "daily":
        if not args.date:
            print("Erreur : --date est obligatoire pour un rapport journalier.")
            return 2
        try:
            report_date = date.fromisoformat(args.date)
        except ValueError:
            print(
                f"Erreur : date invalide : {args.date} "
                "(format attendu AAAA-MM-JJ)"
            )
            return 2
        content = build_daily_report(service.products, orders, report_date)
        filename = f"report_{report_date.isoformat()}.txt"
    else:  # monthly
        if not args.month:
            print("Erreur : --month est obligatoire pour un rapport mensuel.")
            return 2
        try:
            year_text, month_text = args.month.split("-")
            year = int(year_text)
            month = int(month_text)
            date(year, month, 1)
        except (ValueError, AttributeError):
            print(
                f"Erreur : mois invalide : {args.month} "
                "(format attendu AAAA-MM)"
            )
            return 2
        content = build_monthly_report(service.products, orders, year, month)
        filename = f"report_{year:04d}-{month:02d}.txt"

    path = write_report(content, out_dir, filename)
    print(content)
    print()
    print(f"Rapport enregistré dans : {path}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pymart",
        description="PyMart - Gestion d'un magasin en ligne de commande.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sous-commande import
    import_parser = subparsers.add_parser(
        "import", help="Importer des données depuis des fichiers texte."
    )
    import_parser.add_argument("--products", help="Fichier des produits.")
    import_parser.add_argument("--customers", help="Fichier des clients.")
    import_parser.add_argument("--orders", help="Fichier des commandes.")
    import_parser.set_defaults(func=cmd_import)

    # Sous-commande order
    order_parser = subparsers.add_parser("order", help="Gérer les commandes.")
    order_subparsers = order_parser.add_subparsers(
        dest="order_command", required=True
    )

    create_parser = order_subparsers.add_parser(
        "create", help="Créer une commande."
    )
    create_parser.add_argument(
        "--customer", required=True,
        help="Identifiant du client (ex. C001)."
    )
    create_parser.add_argument(
        "--product", required=True,
        help="Identifiant du produit (ex. P001)."
    )
    create_parser.add_argument(
        "--quantity", required=True, type=int,
        help="Quantité commandée."
    )
    create_parser.set_defaults(func=cmd_order_create)

    list_parser = order_subparsers.add_parser(
        "list", help="Afficher les commandes."
    )
    list_parser.set_defaults(func=cmd_order_list)

    # Sous-commande report
    report_parser = subparsers.add_parser(
        "report", help="Générer un rapport."
    )
    report_parser.add_argument(
        "--type", required=True, choices=["daily", "monthly"],
        help="Type de rapport."
    )
    report_parser.add_argument(
        "--date", help="Date du rapport journalier (AAAA-MM-JJ)."
    )
    report_parser.add_argument(
        "--month", help="Mois du rapport mensuel (AAAA-MM)."
    )
    report_parser.add_argument(
        "--out", help="Dossier de sortie des rapports."
    )
    report_parser.set_defaults(func=cmd_report)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PyMartError as error:
        print(f"Erreur : {error}")
        return 1
    except OSError as error:
        print(f"Erreur d'accès au fichier : {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
