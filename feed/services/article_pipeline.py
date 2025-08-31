from django.utils.dateparse import parse_datetime
from datetime import datetime
from feed.scraper.article_scraper import ArticleScraper
import json
import asyncio

def normalize_published(raw):
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, str):
        parsed = parse_datetime(raw)
        return parsed.date() if parsed else None
    return None

# def process_entries(entries: list[dict], site: dict):

#     for art in entries:
#         scraper = ArticleScraper(art["link"])
#         result = scraper.extract_comprehensive()

#         if not result:
#             continue


#         data = {
#             "source": site["name"],
#             "title": result["title"],
#             "link": result["url"],
#             "published": result["date"],
#             "full_content": result["text"],
#         }

#         return data
        

# async def process_links(entries: list, site: dict):

#     for art in entries:
#         scraper = ArticleScraper(art)
#         result = await scraper.extract_comprehensive()

#         if not result:
#             continue


#         data = {
#             "source": site["name"],
#             "title": result["title"],
#             "link": result["url"],
#             "published": result["date"],
#             "full_content": result["text"],
#         }

#         return data
   
async def process_articles(entries: list, site: dict, from_dicts: bool = True) -> list[dict]:
    tasks = []

    for art in entries:
        link = art["link"] if from_dicts else art  
        tasks.append(scrape_article(link, site))

    results = await asyncio.gather(*tasks)
    return [res for res in results if res]  


async def scrape_article(link: str, site: dict) -> dict | None:
    scraper = ArticleScraper(link)
    result = await scraper.extract_comprehensive()

    if not result:
        return None

    return {
        "source": site["name"],
        "title": result["title"],
        "link": result["url"],
        "published": result["date"],
        "full_content": result["text"],
    }