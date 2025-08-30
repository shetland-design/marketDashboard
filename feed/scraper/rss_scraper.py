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

            published = (
            entry.get("published") or
            entry.get("updated") or
            entry.get("pubDate") or
            entry.get("dc_date") or
            None
            )

            # If we have a parsed struct_time, convert to ISO
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6]).isoformat()
            elif not published:
                published = datetime.now().isoformat() 

            articles.append({
                "source": self.source_name,
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": published,
            })
        return articles