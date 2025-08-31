from django.utils.dateparse import parse_datetime
from datetime import datetime
from feed.scraper.article_scraper import ArticleScraper
import json
import asyncio
import logging

def normalize_published(raw):
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, str):
        parsed = parse_datetime(raw)
        return parsed.date() if parsed else None
    return None
   
async def process_articles(entries: list, site: dict, from_dicts: bool = True) -> list[dict]:

    if not entries:
        return []

    semaphore = asyncio.Semaphore(10)

    async def scrape_with_limit(entry):
        async with semaphore:
            link = entry["link"] if from_dicts else entry
            return await scrape_article(link, site)
        
    tasks = [scrape_with_limit(entry) for entry in entries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful_results = []
    for result in results:
        if not isinstance(result, Exception) and result:
            successful_results.append(result)
        elif isinstance(result, Exception):
            logging.error(f"Article processing failed: {result}")

    return successful_results

async def scrape_article(link: str, site: dict) -> dict | None:
    
    try:
        async with ArticleScraper(link) as scraper:
            result = await scraper.extract_comprehensive()

            if not result or not result.get("title"):
                return None
            
            return {
                "source": site["name"],
                "title": result["title"],
                "link": result["url"],
                "published": result["date"],
                "full_content": result["text"]
            }
    
    except Exception as e:
        logging.error(f"Failed to scrape {link}: {e}")
        return None