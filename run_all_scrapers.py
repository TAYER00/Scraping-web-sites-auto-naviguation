import os
import sys
import subprocess
import signal
import time
from typing import Dict, List


print("""

- 1.Lancez python run_all_scrapers.py
- 2.Utilisez les numéros 1-5 pour démarrer/arrêter les scrapers
- 3.Tapez 'q' pour quitter proprement le programme""")


def run_scraper_in_terminal(site_dir: str) -> subprocess.Popen:
    """Lance un scraper dans un nouveau terminal PowerShell."""
    print(f"🚀 Démarrage du scraper pour {site_dir}...")
    
    # Construire la commande Python pour exécuter le scraper
    scraper_path = os.path.join(site_dir, 'scraper.py')
    python_command = f'python "{scraper_path}"'
    
    # Lancer PowerShell avec la commande Python
    process = subprocess.Popen(
        [
            'powershell',
            '-NoExit',  # Garde le terminal ouvert
            '-Command',
            f'cd "{site_dir}"; {python_command}'
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE  # Crée une nouvelle fenêtre de console
    )
    
    print(f"✓ Terminal lancé pour {site_dir} (PID: {process.pid})")
    return process

def main():
    # Liste des sites à scraper
    sites = [
        'agriculture.gov.ma',
        'bkam.ma',
        'cese.ma',
        'finances.gov.ma',
        'oecd.org'
    ]
    
    # Dictionnaire pour stocker les processus
    processes: Dict[str, subprocess.Popen] = {}
    
    print("\n=== Gestionnaire de Scrapers ===\n")
    print("Commandes disponibles :")
    print("1-5: Démarrer/Arrêter le scraper correspondant")
    print("q: Quitter")
    print("\nScrapers :")
    for i, site in enumerate(sites, 1):
        print(f"{i}. {site}")
    
    try:
        while True:
            command = input("\nEntrez une commande (1-5, q pour quitter) : ").lower()
            
            if command == 'q':
                break
            
            try:
                index = int(command) - 1
                if 0 <= index < len(sites):
                    site = sites[index]
                    
                    if site in processes and processes[site].poll() is None:
                        # Arrêter le scraper
                        print(f"⏹️ Arrêt du scraper {site}...")
                        processes[site].terminate()
                        try:
                            processes[site].wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            processes[site].kill()
                        del processes[site]
                        print(f"✓ Scraper {site} arrêté")
                    else:
                        # Démarrer le scraper
                        processes[site] = run_scraper_in_terminal(site)
                else:
                    print("❌ Numéro de scraper invalide")
            except ValueError:
                print("❌ Commande invalide")
    
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé par l'utilisateur...")
    
    finally:
        # Arrêter tous les processus en cours
        for site, process in processes.items():
            if process.poll() is None:
                print(f"⏹️ Arrêt du scraper {site}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        print("\n✨ Programme terminé")

if __name__ == '__main__':
    main()