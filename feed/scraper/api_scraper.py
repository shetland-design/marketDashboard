import httpx

class BackendApiScraper:
    def __init__(self, url: str, source: str, params: dict, parser: callable):
        self.url = url
        self.source = source
        self.params = params
        self.parser = parser

    def fetch_data(self):
        with httpx.Client() as client:
            response = client.get(self.url, params=self.params)
            response.raise_for_status()
            return response.json() 

    def fetch_articles(self):
        data = self.fetch_data()
        return self.parser(data)