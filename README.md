# Web Scraper pour Sites Gouvernementaux Marocains 🇲🇦

Ce projet permet de scraper automatiquement les fichiers PDF des sites web suivants :
- CESE (Conseil Économique, Social et Environnemental)
- Ministère des Finances
- Ministère de l'Agriculture

## Structure du Projet 📁

```
.
├── cese.ma/
│   ├── scraper.py
│   └── pdf_downloads/
├── finances.gov.ma/
│   ├── scraper.py
│   └── pdf_downloads/
├── agriculture.gov.ma/
│   ├── scraper.py
│   └── pdf_downloads/
├── run_all_scrapers.py
└── README.md
```

## Prérequis 🔧

1. Python 3.7 ou supérieur
2. Les bibliothèques Python suivantes :
   ```bash
   pip install playwright beautifulsoup4 requests
   ```
3. Installer les navigateurs Playwright :
   ```bash
   playwright install
   ```

## Utilisation 🚀

### Pour scraper un site spécifique

1. Accédez au répertoire du site souhaité :
   ```bash
   cd cese.ma  # ou oecd.org ou agriculture.gov.ma
   ```

2. Exécutez le scraper :
   ```bash
   python scraper.py
   ```

### Pour scraper tous les sites

Depuis le répertoire principal, exécutez :
```bash
python run_all_scrapers.py
```

## Fonctionnalités ✨

- Crawling récursif intelligent des sites web
- Détection et téléchargement automatique des PDFs
- Organisation des PDFs par site web
- Gestion des erreurs et des timeouts
- Support multilingue (français)
- Gestion des popups de cookies
- Exploration des iframes et du contenu dynamique

## Notes 📝

- Les PDFs sont sauvegardés dans le dossier `pdf_downloads` de chaque site
- Les titres des fichiers sont nettoyés pour être compatibles avec le système de fichiers
- Un système de cache évite de re-télécharger les mêmes PDFs
- La profondeur maximale de crawling est configurable dans chaque scraper

## Limitations ⚠️

- Respecte les règles de robots.txt
- Inclut des délais entre les requêtes pour ne pas surcharger les serveurs
- Ne télécharge que les PDFs des domaines spécifiés