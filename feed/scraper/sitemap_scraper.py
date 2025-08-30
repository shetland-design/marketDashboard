from datetime import datetime
import xml.etree.ElementTree as ET
import requests

class SitemapScraper:
    def __init__(self, feed_url:str):
        self.feed_url = feed_url
        self.namespace = {
            'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }

    def fetch_articles(self, limit: int = None):
        response = requests.get(self.feed_url)
        xml_content = response.text

        root = ET.fromstring(xml_content)
        articles = []

        for url in root.findall('ns:url', self.namespace):
            loc = url.find('ns:loc', self.namespace)
            published = url.find('ns:lastmod', self.namespace)
            if loc is not None:
                articles.append({"link": loc, "published": published})

        return articles       