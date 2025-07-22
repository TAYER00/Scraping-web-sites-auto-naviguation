from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import requests
import time

class AgricultureScraper:
    def __init__(self):
        self.base_url = 'https://www.agriculture.gov.ma/fr'
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
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            context = browser.new_context(
                locale='fr-FR',
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            # Augmenter les timeouts
            page.set_default_timeout(120000)  # 120 secondes
            page.set_default_navigation_timeout(120000)
            
            # Script pour masquer la présence de Playwright
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                window.chrome = { runtime: {} };
            """)
            
            # Configuration pour ignorer les erreurs HTTPS
            context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1'
            })

            def crawl_page(url, depth=0):
                if depth >= max_depth or url in self.visited_urls:
                    return

                print(f"🔍 Exploration de : {url}")
                self.visited_urls.add(url)

                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        # Gérer les erreurs réseau avec une approche progressive
                        for attempt in range(3):
                            try:
                                response = page.goto(url, wait_until='commit', timeout=120000)
                                if response is None:
                                    raise Exception("La navigation a échoué")
                                
                                # Vérifier le statut de la réponse
                                if response.status == 403:
                                    print(f"⚠️ Accès refusé (403) pour {url}, attente de 20 secondes...")
                                    time.sleep(20)
                                    raise Exception("Accès refusé (403)")
                                
                                # Attendre que la page soit complètement chargée
                                page.wait_for_load_state('domcontentloaded', timeout=120000)
                                time.sleep(10)  # Pause plus longue pour laisser le contenu dynamique se charger
                                page.wait_for_load_state('networkidle', timeout=120000)
                                break  # Sortir de la boucle si tout s'est bien passé
                            except Exception as e:
                                if 'net::ERR_NETWORK_CHANGED' in str(e) and attempt < 2:
                                    print(f"⚠️ Changement réseau détecté, nouvelle tentative dans 10 secondes...")
                                    time.sleep(10)
                                    continue
                                raise  # Relancer l'exception si c'est la dernière tentative ou une autre erreur
                        
                        # Gérer le popup des cookies
                        try:
                            if page.locator('text=Les cookies').is_visible():
                                page.click('text=Accepter')
                        except:
                            pass

                        content = page.content()
                        soup = BeautifulSoup(content, 'html.parser')

                        # Chercher les liens PDF dans différentes structures possibles
                        for link in soup.find_all(['a', 'div', 'span'], href=True):
                            href = link.get('href')
                            if not href:
                                continue

                            full_url = urljoin(url, href)

                            if full_url.lower().endswith('.pdf'):
                                if full_url not in self.pdf_links:
                                    self.pdf_links.add(full_url)
                                    title = link.get_text().strip()
                                    print(f"📄 PDF trouvé : {full_url}")
                                    self.download_pdf(full_url, title)
                            elif self.is_valid_url(full_url) and full_url not in self.visited_urls:
                                crawl_page(full_url, depth + 1)

                        # Chercher aussi dans les iframes et les sections dynamiques
                        for frame in page.frames:
                            try:
                                frame_content = frame.content()
                                frame_soup = BeautifulSoup(frame_content, 'html.parser')
                                for link in frame_soup.find_all('a', href=True):
                                    href = link.get('href')
                                    full_url = urljoin(url, href)
                                    if full_url.lower().endswith('.pdf'):
                                        if full_url not in self.pdf_links:
                                            self.pdf_links.add(full_url)
                                            title = link.get_text().strip()
                                            self.download_pdf(full_url, title)
                            except:
                                continue
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
    scraper = AgricultureScraper()
    print("🚀 Démarrage du scraping du site du Ministère de l'Agriculture...")
    scraper.crawl()
    print(f"✨ Terminé! {len(scraper.pdf_links)} PDFs trouvés.")