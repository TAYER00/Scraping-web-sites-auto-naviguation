import os
import sys
from importlib.util import spec_from_file_location, module_from_spec

def import_scraper(path):
    spec = spec_from_file_location("scraper", path)
    module = module_from_spec(spec)
    sys.modules["scraper"] = module
    spec.loader.exec_module(module)
    return module

def run_scraper(site_dir):
    print(f"\n{'='*50}")
    print(f"🎯 Traitement du site: {site_dir}")
    print(f"{'='*50}\n")
    
    scraper_path = os.path.join(site_dir, 'scraper.py')
    
    try:
        # Changer le répertoire de travail
        os.chdir(site_dir)
        
        # Importer et exécuter le scraper
        scraper_module = import_scraper(scraper_path)
        
        # Exécuter le scraper
        if hasattr(scraper_module, 'CESEScraper'):
            scraper = scraper_module.CESEScraper()
        elif hasattr(scraper_module, 'FinancesScraper'):
            scraper = scraper_module.FinancesScraper()
        elif hasattr(scraper_module, 'AgricultureScraper'):
            scraper = scraper_module.AgricultureScraper()
        else:
            raise Exception("Classe de scraper non trouvée")
            
        scraper.crawl()
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution du scraper {site_dir}: {str(e)}")
    finally:
        # Revenir au répertoire principal
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    # Liste des sites à scraper
    sites = ['cese.ma', 'oecd.org', 'agriculture.gov.ma']
    
    print("🚀 Démarrage du scraping de tous les sites...\n")
    
    for site in sites:
        run_scraper(site)
    
    print("\n✨ Scraping terminé pour tous les sites!")

if __name__ == '__main__':
    main()