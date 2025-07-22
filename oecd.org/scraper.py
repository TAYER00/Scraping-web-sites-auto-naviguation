from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import aiohttp
import time
import asyncio
import ssl

class FinancesScraper:
    def __init__(self):
        self.base_url = 'https://www.oecd-ilibrary.org/finance'
        self.target_domain = 'oecd-ilibrary.org'
        time.sleep(5)
        self.visited_urls = set()
        self.pdf_links = set()
        self.download_dir = os.path.join(os.path.dirname(__file__), 'pdf_downloads')
        os.makedirs(self.download_dir, exist_ok=True)

        self.timeout = aiohttp.ClientTimeout(total=60)
        self.resume_file = 'scraping_state.txt'
        self.session = None

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }

    def is_valid_url(self, url):
        try:
            parsed = urlparse(url)
            return self.target_domain in parsed.netloc
        except:
            return False

    async def is_valid_pdf(self, response):
        try:
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type:
                return False
            content_length = int(response.headers.get('Content-Length', 0))
            if content_length < 1024:
                return False
            first_bytes = await response.content.read(4)
            return first_bytes.startswith(b'%PDF')
        except:
            return False

    async def download_pdf(self, url, title):
        try:
            async with self.session.get(url) as response:
                if response.status == 200 and await self.is_valid_pdf(response):
                    filename = title if title.endswith('.pdf') else f"{title}.pdf"
                    filename = ''.join(c for c in filename if c.isalnum() or c in '.-_')[:100]
                    path = os.path.join(self.download_dir, filename)
                    with open(path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(1024):
                            f.write(chunk)
                    print(f"✅ Téléchargé : {filename}")
        except Exception as e:
            print(f"❌ Échec téléchargement {url}: {e}")

    async def extract_pdf_title(self, link, page, url):
        title = link.get_text(strip=True)
        if title and len(title) > 5:
            return title
        for attr in ['title', 'aria-label']:
            value = link.get(attr)
            if value and len(value) > 5:
                return value
        try:
            meta_title = await page.evaluate(
                "() => document.querySelector('meta[name=\"citation_title\"]')?.content || document.querySelector('meta[property=\"og:title\"]')?.content"
            )
            if meta_title and len(meta_title) > 5:
                return meta_title
        except:
            pass
        fallback = os.path.basename(url).replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        return fallback if len(fallback) > 5 else "Document sans titre"

    async def save_state(self):
        try:
            with open(self.resume_file, 'w') as f:
                f.write(','.join(self.visited_urls) + '\n')
                f.write(','.join(self.pdf_links))
        except Exception as e:
            print(f"⚠️ Échec sauvegarde état: {e}")

    async def load_state(self):
        if os.path.exists(self.resume_file):
            try:
                with open(self.resume_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        self.visited_urls = set(lines[0].strip().split(','))
                        if len(lines) > 1:
                            self.pdf_links = set(lines[1].strip().split(','))
            except Exception as e:
                print(f"⚠️ Chargement état échoué: {e}")

    async def check_site_availability(self):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"Tentative {retry_count + 1}/{max_retries}")
                browser = await self.p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu'
                    ]
                )
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    ignore_https_errors=True
                )
                
                page = await context.new_page()
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                await page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                await page.set_extra_http_headers(self.headers)
                
                print("Accès à la page...")
                response = await page.goto(self.base_url, timeout=120000, wait_until='load')
                print("Page chargée, attente du réseau...")
                await page.wait_for_load_state('networkidle', timeout=120000)
                
                if response.status == 403:
                    print("Détection du challenge Cloudflare, attente...")
                    await page.wait_for_timeout(20000)
                    print("Tentative de rechargement...")
                    response = await page.reload(wait_until='load')
                    await page.wait_for_load_state('networkidle', timeout=120000)
                
                print(f"Status code: {response.status}")
                html = await page.content()
                print(f"Longueur du contenu HTML: {len(html)}")
                
                if response.ok:
                    await context.close()
                    await browser.close()
                    return True
                
            except Exception as e:
                print(f"Erreur lors de la tentative {retry_count + 1}: {e}")
            finally:
                try:
                    if 'context' in locals():
                        await context.close()
                    if 'browser' in locals():
                        await browser.close()
                except:
                    pass
            
            retry_count += 1
            if retry_count < max_retries:
                print(f"Attente de 30 secondes avant la prochaine tentative...")
                await asyncio.sleep(30)
        
        print("Nombre maximum de tentatives atteint")
        return False

    async def crawl(self, max_depth=3):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout, connector=connector) as session:
            self.session = session
            await self.load_state()

            async with async_playwright() as p:
                self.p = p
                if not await self.check_site_availability():
                    print("⚠️ Site inaccessible")
                    return

                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                await self.crawl_page(page, self.base_url, 0, max_depth)
                await context.close()
                await browser.close()
                await self.save_state()

    async def crawl_page(self, page, url, depth, max_depth):
        if depth > max_depth or url in self.visited_urls:
            return
        self.visited_urls.add(url)
        try:
            await page.set_extra_http_headers(self.headers)
            response = await page.goto(url, timeout=60000, wait_until='networkidle')
            await page.wait_for_timeout(5000)  # Attendre plus longtemps pour le chargement complet
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if full_url.lower().endswith('.pdf') and full_url not in self.pdf_links:
                    self.pdf_links.add(full_url)
                    title = await self.extract_pdf_title(link, page, full_url)
                    await self.download_pdf(full_url, title)
                elif self.is_valid_url(full_url) and full_url not in self.visited_urls:
                    await self.crawl_page(page, full_url, depth + 1, max_depth)

        except Exception as e:
            print(f"❌ Erreur lors du traitement de {url}: {e}")

if __name__ == '__main__':
    scraper = FinancesScraper()
    asyncio.run(scraper.crawl())
