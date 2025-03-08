# API MediaWiki

Cette implémentation permet d'interagir facilement avec l'API MediaWiki (Wikipedia) en Python.

## Installation

1. Cloner le repository
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

### Interface graphique

Pour lancer l'interface graphique :
```bash
python interface.py
```

L'interface permet de :
- Saisir un terme de recherche
- Afficher les résultats avec leurs titres et extraits
- Naviguer facilement dans les résultats

### Utilisation programmatique

```python
from wiki_api import WikiAPI

# Créer une instance de WikiAPI
wiki = WikiAPI()

# Rechercher des articles
resultats = wiki.rechercher_articles("Python (langage)")
for article in resultats:
    print(f"Titre: {article['title']}")
    print(f"ID: {article['pageid']}")

# Obtenir le contenu d'une page
contenu = wiki.obtenir_contenu_page(page_id=123456)
```

## Fonctionnalités

- `rechercher_articles(terme, limite=10)` : Recherche des articles Wikipedia
- `obtenir_contenu_page(page_id)` : Récupère le contenu d'une page par son ID

## Configuration

Par défaut, l'API utilise l'endpoint français de Wikipedia. Vous pouvez changer cela en passant un autre `base_url` au constructeur :

```python
wiki = WikiAPI(base_url="https://en.wikipedia.org/w/api.php")
``` 