from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import requests
import time

class CESEScraper:
    def __init__(self):
        self.base_url = 'https://www.cese.ma'
        self.visited_urls = set()
        self.pdf_links = set()
        # Utiliser un chemin absolu pour le répertoire de téléchargement
        self.download_dir = os.path.join(os.path.dirname(__file__), 'pdf_downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Configuration de requests pour gérer les erreurs SSL et les timeouts
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = (30, 30)  # (connect timeout, read timeout)
        
        # Configuration des retries pour requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Désactiver les avertissements SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def is_valid_url(self, url):
        try:
            parsed = urlparse(url)
            return parsed.netloc == urlparse(self.base_url).netloc
        except:
            return False

    def download_pdf(self, url, title=None):
        try:
            response = self.session.get(url, stream=True, allow_redirects=True, timeout=30)
            if response.status_code == 200:
                if not title:
                    title = url.split('/')[-1]
                if not title.lower().endswith('.pdf'):
                    title += '.pdf'
                
                # Nettoyer et raccourcir le titre pour un nom de fichier valide
                def clean_filename(filename, max_length=100):
                    # Remplacer les caractères spéciaux par des équivalents simples
                    replacements = {
                        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                        'à': 'a', 'â': 'a', 'ä': 'a',
                        'î': 'i', 'ï': 'i',
                        'ô': 'o', 'ö': 'o',
                        'ù': 'u', 'û': 'u', 'ü': 'u',
                        'ç': 'c',
                        "'": '-', '"': '-',
                        ' ': '-'
                    }
                    for old, new in replacements.items():
                        filename = filename.replace(old, new)
                    
                    # Garder uniquement les caractères alphanumériques et certains symboles
                    filename = ''.join(c for c in filename if c.isalnum() or c in '.-_')
                    
                    # Limiter la longueur du nom de fichier
                    name, ext = os.path.splitext(filename)
                    if len(name) > max_length:
                        name = name[:max_length]
                    return name + ext
                
                title = clean_filename(title)
                filepath = os.path.join(self.download_dir, title)
                
                with open(filepath, 'wb') as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            pdf_file.write(chunk)
                print(f"✅ Téléchargé : {title}")
                return True
        except Exception as e:
            print(f"❌ Erreur de téléchargement {url}: {str(e)}")
        return False

    def crawl(self, max_depth=3):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(
                locale='fr-FR',
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            # Augmenter les timeouts
            page.set_default_timeout(60000)  # 60 secondes
            page.set_default_navigation_timeout(60000)

            def crawl_page(url, depth=0):
                if depth >= max_depth or url in self.visited_urls:
                    return

                print(f"🔍 Exploration de : {url}")
                self.visited_urls.add(url)

                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        page.goto(url)
                        page.wait_for_load_state('networkidle')
                        content = page.content()
                        
                        soup = BeautifulSoup(content, 'html.parser')

                        # Chercher les liens PDF
                        for link in soup.find_all('a', href=True):
                            href = link.get('href')
                            full_url = urljoin(url, href)

                            if full_url.lower().endswith('.pdf'):
                                if full_url not in self.pdf_links:
                                    self.pdf_links.add(full_url)
                                    title = link.get_text().strip()
                                    print(f"📄 PDF trouvé : {full_url}")
                                    self.download_pdf(full_url, title)
                            elif self.is_valid_url(full_url) and full_url not in self.visited_urls:
                                crawl_page(full_url, depth + 1)
                        break  # Si succès, sortir de la boucle
                    except Exception as e:
                        retry_count += 1
                        if 'net::ERR_CONNECTION_RESET' in str(e):
                            print(f"⚠️ Tentative {retry_count}/{max_retries} - Erreur de connexion réinitialisée, nouvelle tentative dans 5 secondes...")
                            time.sleep(5)  # Attendre 5 secondes avant de réessayer
                            if retry_count == max_retries:
                                print(f"❌ Échec après {max_retries} tentatives pour {url}: {str(e)}")
                                return
                            continue
                        else:
                            print(f"❌ Erreur avec {url}: {str(e)}")
                            return

            crawl_page(self.base_url)
            browser.close()

if __name__ == '__main__':
    scraper = CESEScraper()
    print("🚀 Démarrage du scraping du site CESE...")
    scraper.crawl()
    print(f"✨ Terminé! {len(scraper.pdf_links)} PDFs trouvés.")