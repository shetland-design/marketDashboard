from django.utils.dateparse import parse_datetime
from datetime import datetime
from feed.scraper.article_scraper import ArticleScraper
import json


def normalize_published(raw):
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, str):
        parsed = parse_datetime(raw)
        return parsed.date() if parsed else None
    return None

def process_entries(entries: list[dict], site: dict):

    for art in entries:
        scraper = ArticleScraper(art["link"])
        result = scraper.extract_comprehensive()

        if not result:
            continue


        data = {
            "source": site["name"],
            "title": result["title"],
            "link": result["url"],
            "published": result["date"],
            "full_content": result["text"],
        }

        return data
        

def process_links(entries: list, site: dict):

    for art in entries:
        scraper = ArticleScraper(art)
        result = scraper.extract_comprehensive()

        if not result:
            continue


        data = {
            "source": site["name"],
            "title": result["title"],
            "link": result["url"],
            "published": result["date"],
            "full_content": result["text"],
        }

        return data

        

        



    

   
