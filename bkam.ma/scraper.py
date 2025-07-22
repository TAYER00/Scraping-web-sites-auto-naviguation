from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import aiohttp
import time
import asyncio
import ssl
import requests
import json
import signal

class CommuniquesScraper:
    def __init__(self):
        self.base_url = 'https://www.bkam.ma'
        self.data_dir = 'data/communiques'
        self.pdf_dir = 'bkam.ma/pdf_downloads/Communiques/pdf_scraper'
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        self.running = True

    def get_filename_from_url(self, url):
        """Extraire le nom du fichier à partir de l'URL"""
        path = urlparse(url).path
        filename = path.split('/')[-1]
        return f"{filename}.pdf" if not filename.endswith('.pdf') else filename

    def download_pdf(self, url, filename):
        """Télécharger un fichier PDF"""
        filepath = os.path.join(self.pdf_dir, filename)
        
        if os.path.exists(filepath):
            print(f'Le fichier {filename} existe déjà - Ignoré pour optimiser le scraping')
            return True
            
        try:
            print(f'Téléchargement du nouveau fichier: {filename}')
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f'✓ Nouveau PDF téléchargé avec succès: {filename}')
            return True
            
        except requests.exceptions.RequestException as e:
            print(f'❌ Erreur lors du téléchargement du PDF {filename}: {str(e)}')
            if os.path.exists(filepath):
                os.remove(filepath)
            return False

    def get_article_links(self, page):
        """Extraire tous les liens d'articles de la page principale"""
        article_links = []
        links = page.query_selector_all('a.link-item')
        
        for link in links:
            href = link.get_attribute('href')
            if href:
                article_links.append(urljoin(self.base_url, href))
        
        return article_links

    async def scrape(self):
        """Méthode principale pour le scraping des communiqués"""
        print('\n=== Démarrage du scraping des communiqués ===\n')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Variables pour le suivi global
                total_articles_visites = 0
                total_pdfs_trouves = 0
                total_pdfs_telecharges = 0
                tous_articles_sans_pdf = []
                page_courante = 1
                
                while self.running:  # Boucle pour la pagination
                    print(f"\n=== Traitement de la page {page_courante} ===\n")
                    
                    # Construire l'URL avec l'offset approprié
                    offset = (page_courante - 1) * 20
                    # Vérifier si on a atteint la dernière page (offset 1080)
                    if offset > 1080:
                        print("\nDernière page atteinte (offset 1080). Fin du scraping.")
                        break
                    
                    url = urljoin(self.base_url, f'/Communiques?limit=0&block=25bb87ceb25fb0ddf3bb7647b61d0dbd')
                    if offset > 0:
                        url += f'&offset={offset}'
                    
                    print(f"Accès à l'URL: {url}")
                    await page.goto(url)
                    
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    
                    # Attendre que le contenu principal soit chargé
                    await page.wait_for_selector('a.link-item', timeout=60000)
                    
                    # Vérifier si la page contient des articles
                    links = await page.query_selector_all('a.link-item')
                    if not links:
                        print("\nAucun article trouvé sur cette page. Fin du scraping.")
                        break
                    print(f"Nombre de liens trouvés sur la page: {len(links)}")
                    
                    # Récupérer tous les liens d'articles de la page courante
                    article_links = []
                    for link in links:
                        href = await link.get_attribute('href')
                        if href:
                            article_links.append(urljoin(self.base_url, href))
                    print(f"\nNombre d'articles trouvés sur la page {page_courante}: {len(article_links)}")
                    
                    # Liste pour stocker les liens de téléchargement PDF de la page courante
                    pdf_links = []
                    articles_sans_pdf = []
                    articles_visites = 0
                    pdfs_telecharges = 0
                    
                    # Traiter chaque article de la page courante
                    for article_url in article_links:
                        if not self.running:
                            break
                        try:
                            articles_visites += 1
                            total_articles_visites += 1
                            print(f"\nAccès à l'article {articles_visites}/{len(article_links)} de la page {page_courante}: {article_url}")
                            await page.goto(article_url)
                            await page.wait_for_load_state('networkidle')
                            await asyncio.sleep(2)
                            
                            # Chercher le lien du PDF
                            pdf_selector = await page.query_selector('a.link-pdf.pdf')
                            if pdf_selector:
                                pdf_href = await pdf_selector.get_attribute('href')
                                if pdf_href:
                                    full_pdf_url = urljoin(self.base_url, pdf_href)
                                    pdf_links.append({
                                        'url': full_pdf_url,
                                        'filename': self.get_filename_from_url(pdf_href)
                                    })
                                    total_pdfs_trouves += 1
                                    print(f"PDF trouvé: {full_pdf_url}")
                            else:
                                print("Aucun lien PDF trouvé sur cette page.")
                                articles_sans_pdf.append(article_url)
                                tous_articles_sans_pdf.append(article_url)
                                
                        except Exception as e:
                            print(f"Erreur lors du traitement de l'article {article_url}: {str(e)}")
                            articles_sans_pdf.append(article_url)
                            tous_articles_sans_pdf.append(article_url)
                            continue
                    
                    # Télécharger les PDFs trouvés sur la page courante
                    print(f"\nTéléchargement des PDFs de la page {page_courante}...")
                    for pdf_info in pdf_links:
                        if not self.running:
                            break
                        if self.download_pdf(pdf_info['url'], pdf_info['filename']):
                            pdfs_telecharges += 1
                            total_pdfs_telecharges += 1
                    
                    # Afficher le résumé de la page courante
                    print(f"\n=== Résumé de la page {page_courante} ===\n")
                    print(f"Articles visités: {articles_visites}")
                    print(f"PDFs trouvés: {len(pdf_links)}")
                    print(f"PDFs téléchargés: {pdfs_telecharges}")
                    
                    # Passer à la page suivante
                    page_courante += 1
                
                # Afficher le résumé global
                print("\n=== Résumé global du scraping ===\n")
                print(f"Total des pages visitées: {page_courante}")
                print(f"Total des articles visités: {total_articles_visites}")
                print(f"Total des PDFs trouvés: {total_pdfs_trouves}")
                print(f"Total des PDFs téléchargés: {total_pdfs_telecharges}")
                print("\nArticles sans PDF :")
                for url in tous_articles_sans_pdf:
                    print(f"- {url}")
                
            except Exception as e:
                print(f'Erreur lors du scraping: {str(e)}')
            
            finally:
                try:
                    if context:
                        await context.close()
                    if browser:
                        await browser.close()
                except Exception as e:
                    print(f'Erreur lors de la fermeture du navigateur: {str(e)}')
                print('\n=== Scraping terminé ===\n')

    def _save_data(self, communiques):
        """Sauvegarder les données dans un fichier JSON"""
        json_path = os.path.join(self.data_dir, 'communiques.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(communiques, f, ensure_ascii=False, indent=2)
        print(f'Données sauvegardées dans {json_path}')

class DiscoursScraper:
    def __init__(self):
        self.base_url = 'https://www.bkam.ma'
        self.data_dir = 'data/discours'
        self.pdf_dir = 'bkam.ma/pdf_downloads/Discours/pdf_scraper'
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        self.running = True

    def get_filename_from_url(self, url):
        """Extraire le nom du fichier à partir de l'URL"""
        path = urlparse(url).path
        filename = path.split('/')[-1]
        return f"{filename}.pdf" if not filename.endswith('.pdf') else filename

    def download_pdf(self, url, filename):
        """Télécharger un fichier PDF"""
        filepath = os.path.join(self.pdf_dir, filename)
        
        if os.path.exists(filepath):
            print(f'Le fichier {filename} existe déjà - Ignoré pour optimiser le scraping')
            return True
            
        try:
            print(f'Téléchargement du nouveau fichier: {filename}')
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f'✓ Nouveau PDF téléchargé avec succès: {filename}')
            return True
            
        except requests.exceptions.RequestException as e:
            print(f'❌ Erreur lors du téléchargement du PDF {filename}: {str(e)}')
            if os.path.exists(filepath):
                os.remove(filepath)
            return False

    def get_article_links(self, page):
        """Extraire tous les liens d'articles de la page principale"""
        article_links = []
        links = page.query_selector_all('a.link-item')
        
        for link in links:
            href = link.get_attribute('href')
            if href:
                article_links.append(urljoin(self.base_url, href))
        
        return article_links

    async def scrape(self):
        """Méthode principale pour le scraping des discours"""
        print('\n=== Démarrage du scraping des discours ===\n')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Variables pour le suivi global
                total_articles_visites = 0
                total_pdfs_trouves = 0
                total_pdfs_telecharges = 0
                tous_articles_sans_pdf = []
                page_courante = 1
                
                while self.running:  # Boucle pour la pagination
                    print(f"\n=== Traitement de la page {page_courante} ===\n")
                    
                    # Construire l'URL avec l'offset approprié
                    offset = (page_courante - 1) * 20
                    # Vérifier si on a atteint la dernière page (offset 1080)
                    if offset > 1080:
                        print("\nDernière page atteinte (offset 1080). Fin du scraping.")
                        break
                    
                    url = urljoin(self.base_url, f'/Discours?limit=0&block=25bb87ceb25fb0ddf3bb7647b61d0dbd')
                    if offset > 0:
                        url += f'&offset={offset}'
                    
                    print(f"Accès à l'URL: {url}")
                    await page.goto(url)
                    
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    
                    # Attendre que le contenu principal soit chargé
                    await page.wait_for_selector('a.link-item', timeout=60000)
                    
                    # Vérifier si la page contient des articles
                    links = await page.query_selector_all('a.link-item')
                    if not links:
                        print("\nAucun article trouvé sur cette page. Fin du scraping.")
                        break
                    print(f"Nombre de liens trouvés sur la page: {len(links)}")
                    
                    # Récupérer tous les liens d'articles de la page courante
                    article_links = []
                    for link in links:
                        href = await link.get_attribute('href')
                        if href:
                            article_links.append(urljoin(self.base_url, href))
                    print(f"\nNombre d'articles trouvés sur la page {page_courante}: {len(article_links)}")
                    
                    # Liste pour stocker les liens de téléchargement PDF de la page courante
                    pdf_links = []
                    articles_sans_pdf = []
                    articles_visites = 0
                    pdfs_telecharges = 0
                    
                    # Traiter chaque article de la page courante
                    for article_url in article_links:
                        if not self.running:
                            break
                        try:
                            articles_visites += 1
                            total_articles_visites += 1
                            print(f"\nAccès à l'article {articles_visites}/{len(article_links)} de la page {page_courante}: {article_url}")
                            await page.goto(article_url)
                            await page.wait_for_load_state('networkidle')
                            await asyncio.sleep(2)
                            
                            # Chercher le lien du PDF
                            pdf_selector = await page.query_selector('a.link-pdf.pdf')
                            if pdf_selector:
                                pdf_href = await pdf_selector.get_attribute('href')
                                if pdf_href:
                                    full_pdf_url = urljoin(self.base_url, pdf_href)
                                    pdf_links.append({
                                        'url': full_pdf_url,
                                        'filename': self.get_filename_from_url(pdf_href)
                                    })
                                    total_pdfs_trouves += 1
                                    print(f"PDF trouvé: {full_pdf_url}")
                            else:
                                print("Aucun lien PDF trouvé sur cette page.")
                                articles_sans_pdf.append(article_url)
                                tous_articles_sans_pdf.append(article_url)
                                
                        except Exception as e:
                            print(f"Erreur lors du traitement de l'article {article_url}: {str(e)}")
                            articles_sans_pdf.append(article_url)
                            tous_articles_sans_pdf.append(article_url)
                            continue
                    
                    # Télécharger les PDFs trouvés sur la page courante
                    print(f"\nTéléchargement des PDFs de la page {page_courante}...")
                    for pdf_info in pdf_links:
                        if not self.running:
                            break
                        if self.download_pdf(pdf_info['url'], pdf_info['filename']):
                            pdfs_telecharges += 1
                            total_pdfs_telecharges += 1
                    
                    # Afficher le résumé de la page courante
                    print(f"\n=== Résumé de la page {page_courante} ===\n")
                    print(f"Articles visités: {articles_visites}")
                    print(f"PDFs trouvés: {len(pdf_links)}")
                    print(f"PDFs téléchargés: {pdfs_telecharges}")
                    
                    # Passer à la page suivante
                    page_courante += 1
                
                # Afficher le résumé global
                print("\n=== Résumé global du scraping ===\n")
                print(f"Total des pages visitées: {page_courante}")
                print(f"Total des articles visités: {total_articles_visites}")
                print(f"Total des PDFs trouvés: {total_pdfs_trouves}")
                print(f"Total des PDFs téléchargés: {total_pdfs_telecharges}")
                print("\nArticles sans PDF :")
                for url in tous_articles_sans_pdf:
                    print(f"- {url}")
                
            except Exception as e:
                print(f'Erreur lors du scraping: {str(e)}')
            
            finally:
                try:
                    if context:
                        await context.close()
                    if browser:
                        await browser.close()
                except Exception as e:
                    print(f'Erreur lors de la fermeture du navigateur: {str(e)}')
                print('\n=== Scraping terminé ===\n')

    def _save_data(self, discours):
        """Sauvegarder les données dans un fichier JSON"""
        json_path = os.path.join(self.data_dir, 'discours.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(discours, f, ensure_ascii=False, indent=2)
        print(f'Données sauvegardées dans {json_path}')

def signal_handler(signum, frame):
    print("\nSignal d'arrêt reçu. Arrêt en cours...")
    if 'communiques_scraper' in globals():
        communiques_scraper.running = False
    if 'discours_scraper' in globals():
        discours_scraper.running = False

if __name__ == '__main__':
    # Configurer le gestionnaire de signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Créer et exécuter les scrapers
    communiques_scraper = CommuniquesScraper()
    discours_scraper = DiscoursScraper()
    
    # Exécuter les scrapers de manière asynchrone
    async def main():
        try:
            await asyncio.gather(
                communiques_scraper.scrape(),
                discours_scraper.scrape()
            )
        except KeyboardInterrupt:
            print("\nInterruption détectée, arrêt en cours...")
            communiques_scraper.running = False
            discours_scraper.running = False
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScraping interrompu par l'utilisateur.")
    except Exception as e:
        print(f"\nErreur lors de l'exécution: {str(e)}")
    finally:
        print("\nFin du programme.")