from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from datetime import datetime
import json

from feed.scraper import RssScraper, ArticleScraper
from feed.models import NewsArticleModel

class Command(BaseCommand):
    help = "Scrape RSS feeds, extract articles, and save them to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--feeds-per-site",
            type=int,
            default=2,
            help="Number of RSS feed URLs to process per site"
        )
        parser.add_argument(
            "--articles-per-feed",
            type=int,
            default=3,
            help="Number of articles to fetch from each RSS feed"
        )
        parser.add_argument(
            "--sites-file",
            type=str,
            default="feed/conf/sites.json",
            help="Path to the JSON file listing sites and selectors"
        )

    def handle(self, *args, **options):
        feeds_per_site = options["feeds_per_site"]
        articles_per_feed = options["articles_per_feed"]
        sites_file = options["sites_file"]

        try:
            with open(sites_file) as f:
                sites = json.load(f)
        except FileNotFoundError:
            self.stderr.write(f"Sites file not found: {sites_file}")
            return

        for site in sites:
            site_name = site.get("name", "<unknown>")
            self.stdout.write(f"Scraping site: {site_name}")

            for feed_url in site.get("rss_feeds", [])[:feeds_per_site]:
                self.stdout.write(f"  RSS feed: {feed_url}")
                rss = RssScraper(feed_url, site_name)
                articles = rss.fetch_articles(limit=articles_per_feed)

                for art in articles:
                    scraper = ArticleScraper(art["link"], site.get("selectors", {}))
                    result = scraper.get_article_content()

                    if not result or not result.get("content"):
                        self.stdout.write(self.style.WARNING(
                            f"    Failed to extract: {art['title']}"
                        ))
                        continue

                    published_raw = art.get("published")
                    if isinstance(published_raw, datetime):
                        published_date = published_raw.date()
                    elif isinstance(published_raw, str):
                        parsed = parse_datetime(published_raw)
                        published_date = parsed.date() if parsed else None
                    else:
                        published_date = None

                    data = {
                        "source": site_name,
                        "title": art["title"],
                        "link": art["link"],
                        "published": published_date,
                        "summary": art.get("summary", ""),
                        "full_content": result["content"],
                        "categories": art.get("categories", []),
                    }

                    #  ---- Saving the data to the database ----

                    print(f"\n\n\n{data["title"]} \n\n {data['full_content'][:200]}\n\n\n")
                    

                    # try:
                    #     article, created = NewsArticleModel.objects.get_or_create(
                    #         title=data["title"],
                    #         defaults=data
                    #     )
                    #     status = "Saved" if created else "Skipped (duplicate)"
                    #     self.stdout.write(f"    {status}: {data['title']}")
                    # except Exception as e:
                    #     print(f"Error saving {data["title"]}: {e}")


                




            



