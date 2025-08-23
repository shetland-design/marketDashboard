from scraper import RssScraper, ArticleScraper
import json
from .models import NewsArticleModel
from django.utils.dateparse import parse_datetime
from datetime import datetime


with open ("conf/sites.json") as file:
    sites = json.load(file)


for site in sites:
    print(f"Scraping {site['name']}")

    if "rss_feeds" in site:
        
        for feed_url in site["rss_feeds"][:2]:
            rss = RssScraper(feed_url, site['name'])
            articles = rss.fetch_articles(limit=3)
            
            for art in articles:
                article_url = art["link"]
                scraper = ArticleScraper(article_url, site["selectors"])
                result = scraper.get_article_content()
                
                if not result or not result.get("content"):
                    print(f"Could not extract content for: {art['title']}")
                    continue

                published_raw = art.get("published")
                published_date = None
                if isinstance(published_raw, datetime):
                    published_date = published_raw.date()
                elif isinstance(published_raw, str):
                    parsed = parse_datetime(published_raw)
                    published_date = parsed.date() if parsed else None

                data = {
                    "source": site["name"],
                    "title": art["title"],
                    "link": art["link"],
                    "published": published_date,
                    "summary": art.get("summary", ""),
                    "full_content": result["content"],
                    "categories": art.get("categories", [])
                }

                try: 
                    article, created = NewsArticleModel.objects.get_or_create(
                        title=data["title"],
                        defaults=data
                    )
                    status = "Saved" if created else "Skipped (duplicate)"
                    print(f"{status}: {data["title"]}")
                except Exception as e:
                    print(f"Error saving {data["title"]}: {e}")




            



