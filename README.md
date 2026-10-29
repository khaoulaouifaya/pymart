# PyMart

Application de gestion d'un magasin en ligne **en ligne de commande (CLI)**,
réalisée dans le cadre d'un projet de l'école en Python.

Le programme utilise uniquement la **bibliothèque standard Python** : aucune
dépendance externe, aucune base de données, aucune interface web.

---

## 1. Présentation du projet

PyMart permet de gérer simplement un petit magasin :

- importer des **produits**, des **clients** et des **commandes** depuis des
  fichiers texte ;
- vérifier et nettoyer les données importées ;
- créer de nouvelles commandes (avec contrôle du stock) ;
- afficher les commandes ;
- générer des **rapports journaliers et mensuels** enregistrés sur le disque ;
- conserver les données entre deux lancements grâce à un fichier JSON local.

Le code est volontairement simple, lisible et découpé en petits modules pour
être facile à expliquer.

---

## 2. Fonctionnalités

- Importation de produits, clients et commandes depuis des fichiers texte.
- Nettoyage des données : espaces, lignes vides, commentaires, majuscules.
- Validation : identifiants, prix, quantités, dates, doublons, références.
- Création de commandes avec vérification du stock et des identifiants.
- Génération de rapports journaliers et mensuels (fichiers `.txt`).
- Sauvegarde automatique dans `data/pymart_store.json`.
- Gestion des erreurs sans plantage : les lignes invalides sont signalées
  et ignorées, les autres continuent d'être importées.

---

## 3. Structure des dossiers

```text
pymart-project/
├── pymart/
│   ├── __init__.py      # marque le dossier comme un package Python
│   ├── cli.py           # interface en ligne de commande (argparse)
│   ├── models.py        # classes Product, DigitalProduct, Customer, Order
│   ├── parsers.py       # lecture et validation des fichiers d'import
│   ├── services.py      # logique métier (PyMartService, OrderService)
│   ├── reports.py       # génération des rapports journaliers et mensuels
│   ├── storage.py       # sauvegarde et chargement des données (JSON)
│   └── exceptions.py    # exceptions personnalisées
├── data/
│   ├── products.txt     # produits de démonstration
│   ├── customers.txt    # clients de démonstration
│   ├── orders.txt       # commandes de démonstration
│   └── reports/         # rapports générés (créé automatiquement)
├── data-invalid/        # fichiers avec des données invalides (démonstration)
├── tests/               # tests unitaires (unittest)
└── README.md
```

> Les fichiers `data/*.txt` sont des **sources** : ils ne sont jamais modifiés.
> L'état du magasin est enregistré séparément dans `data/pymart_store.json`.

---

## 4. Prérequis

- **Python 3.10 ou supérieur** (vérifier avec `python3 --version`).
- Aucun module externe à installer.

---

## 5. Instructions pour démarrer

Ouvrir un terminal dans le dossier du projet :

```bash
cd pymart-project
```

Importer les données de démonstration :

```bash
python3 -m pymart.cli import \
  --products data/products.txt \
  --customers data/customers.txt \
  --orders data/orders.txt
```

C'est tout : les données sont importées, nettoyées et sauvegardées.

---

## 6. Commandes CLI à exécuter

Toutes les commandes se lancent **depuis la racine du projet**.

```bash
# Aide générale
python3 -m pymart.cli --help

# Importer les données
python3 -m pymart.cli import --products data/products.txt --customers data/customers.txt --orders data/orders.txt

# Créer une commande
python3 -m pymart.cli order create --customer C001 --product P001 --quantity 2

# Afficher les commandes
python3 -m pymart.cli order list

# Rapport journalier
python3 -m pymart.cli report --type daily --date 2026-06-30 --out reports/

# Rapport mensuel
python3 -m pymart.cli report --type monthly --month 2026-06 --out reports/
```

### Format des fichiers d'import

- **Produits** : `product_id;name;price;quantity;type`
  (`type` vaut `physical` ou `digital` et peut être omis).
- **Clients** : `customer_id;name;email`
- **Commandes** : `order_id;customer_id;product_id;quantity;order_date`
  (date au format `AAAA-MM-JJ`).

Le séparateur `|` est aussi accepté lorsqu'il n'y a pas d'ambiguïté.
Les lignes vides et celles qui commencent par `#` sont ignorées.

---

## 7. Description des principales classes

| Classe | Rôle |
| --- | --- |
| `Product` | Produit du magasin : prix, quantité en stock, gestion du stock. |
| `DigitalProduct` | Produit dématérialisé (hérite de `Product`, stock illimité). |
| `Customer` | Client du magasin. |
| `Order` | Commande : client, produit, quantité, date, montant total. |
| `OrderService` | Création des commandes, vérifications, gestion du stock. |
| `PyMartService` | Contient toutes les données et orchestre les importations. |

Les montants financiers utilisent `Decimal` pour éviter les erreurs
d'arrondi des nombres flottants.

---

## 8. Concepts Python utilisés

### Héritage

`DigitalProduct` **hérite** de `Product` : il récupère automatiquement ses
attributs (`product_id`, `name`, `price`) et ses méthodes (`get_price`).

### Polymorphisme

`DigitalProduct` **redéfinit** `is_available`, `decrease_stock` et `display`.
Le service appelle ces méthodes sans savoir si le produit est physique ou
numérique : le comportement s'adapte automatiquement. C'est le polymorphisme.

### Exceptions personnalisées

Le fichier `exceptions.py` définit `PyMartError` et ses sous-classes
(`DataValidationError`, `UnknownProductError`, `DuplicateIdError`, etc.).
Elles permettent d'afficher des messages clairs sans faire planter le
programme.

### Générateurs (`yield`)

La fonction `read_lines` de `parsers.py` est un générateur : elle lit un
fichier **ligne par ligne** sans charger tout le fichier en mémoire.

---

## 9. Instructions pour générer les rapports

Les rapports sont enregistrés dans le dossier indiqué par `--out`
(par défaut `data/reports`), créé automatiquement si nécessaire.

```bash
# Rapport journalier pour le 30 juin 2026
python3 -m pymart.cli report --type daily --date 2026-06-30 --out reports/

# Rapport mensuel pour juin 2026
python3 -m pymart.cli report --type monthly --month 2026-06 --out reports/
```

Les fichiers produits sont :

- `report_2026-06-30.txt` pour le rapport journalier ;
- `report_2026-06.txt` pour le rapport mensuel.

Les rapports sont **reproductibles** : les mêmes données et la même période
donnent toujours exactement le même contenu.

---

## 10. Instructions pour lancer les tests

Depuis la racine du projet :

```bash
python3 -m unittest discover -s tests -v
```

Les tests couvrent : les objets, le calcul des prix, l'héritage et le
polymorphisme, la validation des fichiers, les exceptions, la création de
commandes, les stocks insuffisants, les identifiants en double, les rapports
et la persistance.

---

## Démonstration pour le professeur

Suivre ces étapes dans l'ordre et réaliser une capture d'écran de chacune.

1. **Vérifier la version de Python** :

   ```bash
   python3 --version
   ```

2. **Afficher l'aide** :

   ```bash
   python3 -m pymart.cli --help
   ```

3. **Importer les données** :

   ```bash
   python3 -m pymart.cli import --products data/products.txt --customers data/customers.txt --orders data/orders.txt
   ```

   → capture du message « Total des enregistrements ajoutés : 19 ».

4. **Créer une commande** :

   ```bash
   python3 -m pymart.cli order create --customer C001 --product P001 --quantity 2
   ```

   → capture de la commande créée (identifiant `ORD009`).

5. **Afficher les commandes** :

   ```bash
   python3 -m pymart.cli order list
   ```

6. **Tester la gestion des erreurs** (produit inconnu) :

   ```bash
   python3 -m pymart.cli order create --customer C001 --product P999 --quantity 1
   ```

   → capture du message « Erreur : Produit inconnu : P999 ».

7. **Générer le rapport journalier** :

   ```bash
   python3 -m pymart.cli report --type daily --date 2026-06-30 --out reports/
   ```

8. **Générer le rapport mensuel** :

   ```bash
   python3 -m pymart.cli report --type monthly --month 2026-06 --out reports/
   ```

9. **Montrer la persistance** : fermer le terminal, en rouvrir un, puis :

   ```bash
   python3 -m pymart.cli order list
   ```

   → les données sont toujours là (fichier `data/pymart_store.json`).

10. **Montrer les données invalides** :

    ```bash
    python3 -m pymart.cli import --products data-invalid/products_invalid.txt --customers data-invalid/customers_invalid.txt --orders data-invalid/orders_invalid.txt
    ```

    → capture des messages `[ERREUR]` ligne par ligne.

11. **Lancer les tests** :

    ```bash
    python3 -m unittest discover -s tests -v
    ```

    → capture du résultat « OK ».
