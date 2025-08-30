from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from datetime import datetime
import json

from feed.scraper.api_scraper import BackendApiScraper
from feed.models import NewsArticleModel
from feed.scraper.utils import build_api_params, load_config
from feed.scraper.rss_scraper import RssScraper
from feed.scraper.article_scraper import ArticleScraper
from feed.scraper.sitemap_scraper import SitemapScraper
from feed.parsers.reuters import reuters_parser
from feed.services.article_pipeline import process_entries, process_links
from feed.parsers import PARSER_REGISTRY
from feed.services.saving_to_db import save_article


class Command(BaseCommand):
    help = "Scrape RSS feeds, extract articles, and save them to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--feeds-per-site",
            type=int,
            default=1,
            help="Number of RSS feed URLs to process per site"
        )
        parser.add_argument(
            "--articles-per-feed",
            type=int,
            default=1,
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
            sites = load_config(sites_file)
        except FileNotFoundError:
            self.stderr.write(f"Sites file not found: {sites_file}")
            return

        for site in sites:

            site_name = site.get("name", "<unknown>")
            self.stdout.write(f"\n=== Scraping site: {site_name} ===")

            if site.get("type") == "rss":
                self._run_rss(site, feeds_per_site, articles_per_feed)

            elif site.get("type") == "normal":
                self._run_api(site, feeds_per_site, articles_per_feed)
            
            elif site.get("type") == "sitemap":
                self._run_sitemap(site, feeds_per_site, articles_per_feed)

            else:
                self.stderr.write(f"Unknown site type: {site.get('type')}")

    def _run_sitemap(self, site: dict, feeds_per_site: int, articles_per_feed: int):
        for url in site.get("sitemaps", [])[:feeds_per_site]:
            self.stdout.write(f"Sitemap: {url}")
            sitemap = SitemapScraper(url)
            links = sitemap.fetch_articles(limit=articles_per_feed)
            process_links(links, site)
            
        

    def _run_rss(self, site: dict, feeds_per_site: int, articles_per_feed: int):
        for feed_url in site.get("rss_feeds", [])[:feeds_per_site]:
            self.stdout.write(f"  • RSS feed: {feed_url}")
            rss = RssScraper(feed_url, site["name"])
            entries = rss.fetch_articles(limit=articles_per_feed)
            data = process_entries(entries, site)
            save_article(data)
            

    def _run_api(self, site: dict, feeds_per_site: int, articles_per_feed: int):

        if site["categories"]:
            for cat in site["categories"][:feeds_per_site]:

                scraper = BackendApiScraper(
                base_url=site["base_url"],
                url = site["url"],
                source=site["name"],
                category=cat,
                selectors=site["selectors"]
                )

                links = scraper.fetch_article_links(limit=articles_per_feed)
                data = process_links(links, site)
                save_article(data)

        else: 

            scraper = BackendApiScraper(
                base_url=site["base_url"],
                url = site["url"],
                source=site["name"],
                selectors=site["selectors"]
                )
            
            links = scraper.fetch_article_links(limit=articles_per_feed)
            data = process_links(links, site)
            save_article(data)


                

        

        
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


                




            



