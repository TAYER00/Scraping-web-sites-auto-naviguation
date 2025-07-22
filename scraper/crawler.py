import os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
from .models import Website, ScrapedPDF

class WebCrawler:
    def __init__(self, website):
        self.website = website
        self.visited_urls = set()
        self.pdf_links = set()
        self.base_domain = urlparse(website.url).netloc

    def is_valid_url(self, url):
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.base_domain
        except:
            return False

    def is_pdf_link(self, url):
        return url.lower().endswith('.pdf')

    def download_pdf(self, url, title):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Create directory if it doesn't exist
                pdf_dir = os.path.join('pdf_downloads', self.base_domain)
                os.makedirs(pdf_dir, exist_ok=True)
                
                # Create filename from title
                filename = f"{title[:100]}.pdf"  # Limit filename length
                filepath = os.path.join(pdf_dir, filename)
                
                with open(filepath, 'wb') as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            pdf_file.write(chunk)
                
                # Save to database
                ScrapedPDF.objects.create(
                    website=self.website,
                    title=title,
                    url=url,
                    file_path=filepath
                )
                return True
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
        return False

    def crawl(self, max_depth=3):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            def crawl_page(url, depth=0):
                if depth >= max_depth or url in self.visited_urls:
                    return

                self.visited_urls.add(url)
                try:
                    page.goto(url)
                    page.wait_for_load_state('networkidle')
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')

                    # Find all links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        full_url = urljoin(url, href)

                        if self.is_pdf_link(full_url):
                            if full_url not in self.pdf_links:
                                self.pdf_links.add(full_url)
                                title = link.get_text().strip() or os.path.basename(full_url)
                                self.download_pdf(full_url, title)
                        elif self.is_valid_url(full_url):
                            crawl_page(full_url, depth + 1)

                except Exception as e:
                    print(f"Error crawling {url}: {str(e)}")

            crawl_page(self.website.url)
            browser.close()

def start_crawling(website_url, website_name):
    website = Website.objects.create(name=website_name, url=website_url)
    crawler = WebCrawler(website)
    crawler.crawl()
    return crawler.pdf_links