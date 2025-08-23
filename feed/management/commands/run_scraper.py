from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from datetime import datetime
import json

from feed.scraper.api_scraper import BackendApiScraper
from feed.models import NewsArticleModel
from feed.scraper.utils import build_api_params
from feed.scraper.rss_scraper import RssScraper
from feed.scraper.article_scraper import ArticleScraper
from feed.parsers.reuters import reuters_parser
from feed.services.article_pipeline import process_entries


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

            kind = site["type"]

            site_name = site.get("name", "<unknown>")
            self.stdout.write(f"Scraping site: {site_name}")

            if kind == "rss":
                self._run_rss(site, feeds_per_site, articles_per_feed)

            elif kind == "api":
                self._run_api(site, reuters_parser)

    def _run_rss(self, site: dict, feeds_per_site: int, articles_per_feed: int):
        for feed_url in site.get("rss_feeds", [])[:feeds_per_site]:
            self.stdout.write(f"  • RSS feed: {feed_url}")
            rss = RssScraper(feed_url, site["name"])
            entries = rss.fetch_articles(limit=articles_per_feed)
            process_entries(entries, site)

    def _run_api(self, site: dict, parser_func: callable):
        api_cfg = site["api"]
        params = build_api_params(api_cfg["params"])

        scraper = BackendApiScraper(
            url=api_cfg["url"],
            source=site["name"],
            params=params,
            parser=parser_func
            )

        entries = scraper.fetch_articles()
        process_entries(entries, site)

            #  ---- Saving the data to the database ----
                    
            # try:
            #    article, created = NewsArticleModel.objects.get_or_create(
            #    title=data["title"],
            #    defaults=data
            #    )
            #     status = "Saved" if created else "Skipped (duplicate)"
            #     self.stdout.write(f"    {status}: {data['title']}")
            # except Exception as e:
            #     print(f"Error saving {data["title"]}: {e}")  


                




            



