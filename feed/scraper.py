import feedparser
from datetime import datetime
import trafilatura
import httpx
from selectolax.parser import HTMLParser
import re

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"}

class RssScraper:
    def __init__(self, feed_url:str, source_name: str):
        self.feed_url = feed_url
        self.source_name = source_name

    def fetch_articles(self, limit: int = None):
        feed = feedparser.parse(self.feed_url)
        articles = []
        entries = feed.entries if limit is None else feed.entries[:limit]

        for entry in entries:

            categories = []
            
            if 'tags' in entry:
                categories = [tag['term'] for tag in entry.tags if 'term' in tag]

            articles.append({
                "source": self.source_name,
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", datetime.now().isoformat()),
                "categories": categories
            })
        return articles
    






class ArticleScraper:
    def __init__(self, url, selector):
        self.url = url
        self.selector = selector

    def fetch_article_page(self):
        try: 
            resp = httpx.get(self.url, headers=headers)
            resp.raise_for_status()
            return resp.text
        except httpx.RequestError as e:
            print(f"Request failed for {self.url}: {e}")
        except httpx.HTTPStatusError as e:
            print(f"Bad status {e.response.status_code} for {self.url}")
        return None

    def ends_with_phrase(self, p):
        last_words = p
        return any(last_words.endswith(phrase) for phrase in self.selector.get("bad_endings", []))

    
    def clean_text(self, text: str) -> str:
        return " ".join(text.split())


    def get_article_content(self):
        page = self.fetch_article_page()
        if not page:
            return None

        html = HTMLParser(page)

        container_selector = self.selector["article_container"]
        articles_selector = self.selector["article_content"]

        if container_selector:
            container = html.css_first(container_selector)
            content = container.css(articles_selector)
        else: 
            content = html.css(articles_selector)

        paragraphs = [self.clean_text(p.text(strip=True)) for p in content if p.text()]

        if paragraphs and self.ends_with_phrase(paragraphs[-1]):
            paragraphs = paragraphs[:-1]

        full_text = "".join(paragraphs)

        return {
            "content": full_text,
            "length": len(full_text.split())
        }

    

            






    

