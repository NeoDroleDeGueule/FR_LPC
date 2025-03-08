import requests
from typing import Dict, List, Optional

class WikiAPI:
    def __init__(self, base_url: str = "https://www.mediawiki.org/w/api.php"):
        self.base_url = base_url
        self.session = requests.Session()

    def rechercher_articles(self, terme: str, limite: int = 10) -> List[Dict]:
        """
        Recherche des articles MediaWiki correspondant au terme donné.
        
        Args:
            terme: Le terme à rechercher
            limite: Nombre maximum de résultats à retourner
            
        Returns:
            Liste de dictionnaires contenant les informations des articles
        """
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": terme,
            "srlimit": limite
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        
        resultats = response.json()
        return resultats["query"]["search"]

    def obtenir_contenu_page(self, page_id: int) -> Optional[str]:
        """
        Récupère le contenu d'une page MediaWiki par son ID.
        
        Args:
            page_id: L'identifiant de la page
            
        Returns:
            Le contenu de la page ou None si non trouvé
        """
        params = {
            "action": "parse",
            "format": "json",
            "pageid": page_id,
            "prop": "text"
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        
        resultats = response.json()
        if "parse" in resultats and "text" in resultats["parse"]:
            return resultats["parse"]["text"]["*"]
        return None

    def obtenir_contenu_brut(self, titre: str) -> Optional[str]:
        """
        Récupère le contenu brut d'une page MediaWiki par son titre.
        
        Args:
            titre: Le titre de la page
            
        Returns:
            Le contenu brut de la page ou None si non trouvé
        """
        params = {
            "action": "query",
            "format": "json",
            "titles": titre,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main"
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        
        # Prendre la première page trouvée
        for page_id in pages:
            page = pages[page_id]
            if "revisions" in page:
                return page["revisions"][0]["slots"]["main"]["*"]
        return None

# Exemple d'utilisation
if __name__ == "__main__":
    wiki = WikiAPI()
    
    # Recherche d'articles
    resultats = wiki.rechercher_articles("Python (langage)")
    for article in resultats:
        print(f"Titre: {article['title']}")
        print(f"ID: {article['pageid']}")
        print("---") 