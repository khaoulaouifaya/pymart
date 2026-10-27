"""Exceptions personnalisées du projet PyMart.

Toutes les erreurs de l'application héritent de PyMartError afin de pouvoir
les attraper facilement dans l'interface en ligne de commande.
"""


class PyMartError(Exception):
    """Classe de base pour toutes les erreurs de PyMart."""


class DataValidationError(PyMartError):
    """Donnée invalide (prix, quantité, identifiant, etc.)."""


class RecordFormatError(PyMartError):
    """Une ligne d'un fichier d'importation n'a pas le bon format."""


class UnknownProductError(PyMartError):
    """Référence à un produit inexistant."""


class UnknownCustomerError(PyMartError):
    """Référence à un client inexistant."""


class DuplicateIdError(PyMartError):
    """Identifiant déjà présent (doublon)."""


class InsufficientStockError(PyMartError):
    """Stock insuffisant pour honorer une commande."""
