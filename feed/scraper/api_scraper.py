import httpx
from selectolax.parser import HTMLParser
from datetime import datetime
import asyncio
import logging

class BackendApiScraper:
    def __init__(self, url: str, source: str, selectors: dict, base_url: str, category: str = None):
        self.url = url
        self.base_url = base_url
        self.source = source
        self.category = category
        self.selectors = selectors
        self.headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}
        self.final_url = self.prepare_url(self.url)

    def prepare_url(self, url_template):
        now = datetime.now()
        year = now.year
        month = f"{now.month:02d}"

        if "{year}" in url_template or "{month}" in url_template:
            return url_template.format(year=year, month=month)
        
        if "{category}" in url_template and self.category:
            return url_template.format(category=self.category)

        return url_template
        
    async def fetch_data_async(self):
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            try:
                response = await client.get(self.final_url)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logging.error(f"Failed to fetch {self.final_url}: {e}")
                return None
            
    async def fetch_article_links_async(self, limit: int = None):
        html_content = await self.fetch_data_async()
        if not html_content:
            return []
        
        def parse_links():
            tree = HTMLParser(html_content)

            if self.selectors.get("container"):
                container = tree.css_first(self.selectors["container"])
                if not container:
                    container = tree
            else:
                container = tree

            links = []
            for node in container.css(self.selectors["articles"]):
                href = node.attributes.get("href")
                if href:
                    if not href.startswith("http"):
                        href = f"{self.base_url.rstrip('/')}/{href.lstrip('/')}"
                    links.append(href)

            return links[:limit] if limit else links
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, parse_links)
    
    def fetch_article_links(self, limit: int = None):
        return asyncio.run(self.fetch_article_links_async(limit))

   

        