import feedparser
from datetime import datetime

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