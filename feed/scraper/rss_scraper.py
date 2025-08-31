import feedparser
from datetime import datetime
import asyncio
import aiohttp


class RssScraper:
    def __init__(self, feed_url:str, source_name: str):
        self.feed_url = feed_url
        self.source_name = source_name

    # This uses async(aiohttp) to get the raw xml text because feedparser doesn't support async.

    async def fetch_feed_text(self, session: aiohttp.ClientSession) -> str:
        async with session.get(self.feed_url, timeout=10, allow_redirects=True) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def fetch_articles(self, session: aiohttp.ClientSession, limit: int = None):
        raw_feed = await self.fetch_feed_text(session)
        feed = feedparser.parse(raw_feed)

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