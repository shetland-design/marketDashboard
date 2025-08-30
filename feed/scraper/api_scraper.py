import httpx
from selectolax.parser import HTMLParser
from datetime import datetime

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
        
    def fetch_data(self):
        with httpx.Client(headers=self.headers) as client:
            response = client.get(self.final_url)
            print(response.raise_for_status())
            return response.text

    def fetch_container(self):
        tree = HTMLParser(self.fetch_data())
        container = tree.css_first(self.selectors["container"])
        return container
    
    def fetch_article_links(self, limit: int = None):
        if self.selectors["container"]:
            contain = self.fetch_container()
        contain = HTMLParser(self.fetch_data())
        links = []

        for node in contain.css(self.selectors["articles"]):
            if node.attributes.get('href'):
                link = node.attributes.get('href')
                if self.base_url not in link:
                    link = f"{self.base_url}{link}"
            links.append(link)

        result = links if limit is None else links[:limit]
        print(result)
        return result



        