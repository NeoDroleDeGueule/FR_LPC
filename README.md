# Application de Transcription Phonétique LPC

Cette application web permet de transcrire du texte français en notation phonétique, en utilisant une combinaison de l'API Wiktionary et d'un système de règles phonétiques personnalisé.

## Fonctionnalités

- Transcription phonétique de texte français
- Interface web simple et intuitive
- Système hybride utilisant :
  - API Wiktionary pour les mots courants
  - Système de règles phonétiques comme solution de repli
- Support des caractères spéciaux français
- Gestion des liaisons phonétiques

## Installation locale

1. Clonez le dépôt :
```bash
git clone https://github.com/NeoDroleDeGueule/FR_LPC.git
cd FR_LPC
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancez l'application :
```bash
python app.py
```

L'application sera accessible à l'adresse : http://127.0.0.1:5000

## Utilisation

1. Accédez à l'application via votre navigateur
2. Entrez le texte à transcrire dans le champ prévu
3. Cliquez sur le bouton "Transcrire" ou utilisez Ctrl+Enter
4. La transcription phonétique apparaîtra en dessous

## Déploiement

L'application est déployée sur Render.com et accessible à l'adresse : [URL_DE_VOTRE_APP]

## Structure du projet

```
FR_LPC/
├── app.py              # Application Flask principale
├── templates/          # Templates HTML
│   └── index.html     # Interface utilisateur
├── requirements.txt    # Dépendances Python
├── gunicorn.conf.py   # Configuration du serveur
└── render.yaml        # Configuration de déploiement
```

## Variables d'environnement

L'application utilise les variables d'environnement suivantes :
- `FLASK_ENV` : Environnement Flask (development/production)
- `FLASK_DEBUG` : Mode debug (0/1)
- `PORT` : Port du serveur (par défaut: 5000)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 