from django.utils.dateparse import parse_datetime
from datetime import datetime
from feed.models import NewsArticleModel
from feed.scraper.article_scraper import ArticleScraper

def normalize_published(raw):
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, str):
        parsed = parse_datetime(raw)
        return parsed.date() if parsed else None
    return None

def process_entries(entries: list[dict], site: dict):
    for art in entries:
        scraper = ArticleScraper(art["link"], site.get("selectors", {}))
        result = scraper.get_article_content()

        if not result or not result.get("content"):
            continue

        published_date = normalize_published(art.get("published"))
        data = {
            "source":     site["name"],
            "title":      art["title"],
            "link":       art["link"],
            "published":  published_date,
            "summary":    art.get("summary", ""),
            "full_content": result["content"],
            "categories": art.get("categories", []),
        }
