from datetime import datetime
import xml.etree.ElementTree as ET
import httpx
import asyncio
import logging

class SitemapScraper:
    def __init__(self, feed_url:str):
        self.feed_url = feed_url
        self.namespace = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }

    async def fetch_articles_async(self, limit: int = None):

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:

                response = await client.get(self.feed_url)
                response.raise_for_status()
                xml_content = response.text
            except Exception as e:
                logging.error(f"Failed to fetch sitemap {self.feed_url}: {e}")
                return []

        def parse_sitemap():
            try: 
                root = ET.fromstring(xml_content)
                articles = []

                for url in root.findall('ns:url', self.namespace):
                    loc = url.find('ns:loc', self.namespace)
                    lastmod = url.find('ns:lastmod', self.namespace)

                    if loc is not None:
                        articles.append({
                            "link": loc.text,
                            "published": lastmod.text if lastmod is not None else None
                        })

                return articles[:limit] if limit else articles
            
            except ET.ParseError as e:
                logging.error(f"Failed to parse sitemap XML: {e}")
                return []
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, parse_sitemap)
    
    def fetch_articles(self, limit: int = None):
        return asyncio.run(self.fetch_articles_async(limit))

            
