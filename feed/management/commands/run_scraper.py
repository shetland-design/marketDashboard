from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from datetime import datetime
import json
import asyncio
import aiohttp
import logging

from feed.scraper.api_scraper import BackendApiScraper
from feed.models import NewsArticleModel
from feed.scraper.utils import build_api_params, load_config
from feed.scraper.rss_scraper import RssScraper
from feed.scraper.article_scraper import ArticleScraper
from feed.scraper.sitemap_scraper import SitemapScraper
from feed.parsers.reuters import reuters_parser
from feed.services.article_pipeline import process_articles
from feed.parsers import PARSER_REGISTRY
from feed.services.saving_to_db import save_articles


class Command(BaseCommand):
    help = "Scrape RSS feeds, extract articles, and save them to the database"

    def add_arguments(self, parser):
        parser.add_argument("--feeds-per-site", type=int, default=1)
        parser.add_argument("--articles-per-feed", type=int, default=1)
        parser.add_argument("--sites-file", type=str, default="feed/conf/sites.json")
        parser.add_argument("--max-concurrent", type=int, default=10)

    def handle(self, *args, **options):
        asyncio.run(self._handle_async(**options))

    async def _handle_async(self, **options):

        try:
            sites = load_config(options["sites_file"])
        except FileNotFoundError:
            self.stderr.write(f"Sites file not found: {options['sites_file']}")
            return
        
        semaphore = asyncio.Semaphore(options["max_concurrent"])

        async def process_site_with_limit(site):
            async with semaphore:
                return await self._process_site(site, options)
            
        tasks = [process_site_with_limit(site) for site in sites]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if not isinstance(r, Exception))
        self.stdout.write(f"Processed {successful}/{len(sites)} sites successfully")

    async def _process_site(self, site:dict, options: dict):
        site_name = site.get("name", "<unknown>")
        self.stdout.write(f"Processing site: {site_name}")

        try: 
            if site.get("type") == "rss":
                return await self._run_rss_optimized(site, options)
            elif site.get("type") == "normal":
                return await self._run_api_optimized(site, options)
            elif site.get("type") == "sitemap":
                return await self._run_sitemap_optimized(site, options)
            else:
                self.stderr.write(f"Unknown site type: {site.get('type')}")
                return None
        except Exception as e:
            self.stderr.write(f"Error processing {site_name}: {e}")
            return None
        

    # RSS scraper

    
    async def _run_rss_optimized(self, site: dict, options: dict):
        feeds_urls = site.get("rss_feeds", [])[:options["feeds_per_site"]]

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=50)
        ) as session:
            rss_tasks = []
            for feed_url in feeds_urls:
                scraper = RssScraper(feed_url, site["name"])
                rss_tasks.append(scraper.fetch_articles(session, limit=options["articles_per_feed"]))

            feed_results = await asyncio.gather(*rss_tasks, return_exceptions=True)

            all_entries = []
            for entries in feed_results:
                if not isinstance(entries, Exception) and entries:
                    all_entries.extend(entries)

            if not all_entries:
                return []
            
            batch_size = 20
            all_articles = []

            for i in range(0, len(all_entries), batch_size):
                batch = all_entries[i:i + batch_size]
                batch_articles = await process_articles

                if batch_articles:
                    await save_articles(batch_articles)
                    all_articles.extend(batch_articles)

                await asyncio.sleep(0.5)

            return all_articles
        


    # API scraper - Basically means the static site with no RSS or sitemap



    async def _run_api_optimized(self, site: dict, options: dict):
        all_articles = []

        if site.get("categories"):
            categories = site["categories"][:options["feeds_per_site"]]

            category_tasks = []
            for category in categories:
                category_tasks.append(
                    self._process_api_category(site, category, options["articles_per_feed"])
                )
            results = await asyncio.gather(*category_tasks, return_exceptions=True)
            
            for result in results:
                if not isinstance(result, Exception) and result:
                    all_articles.extend(result)

        else:

            articles = await self._process_api_category(site, None, options["articles_per_feed"])
            if articles:
                all_articles.extend(articles)

        return all_articles
    
    async def _process_api_category(self, site: dict, category: str, limit: int):
        try:
            scraper = BackendApiScraper(
                base_url=site["base_url"],
                url=site["url"],
                source=site["name"],
                category=category,
                selectors=site["selectors"]
                )

            links = await scraper.fetch_article_async(limit=limit)

            if links:
                articles = await process_articles(links, site, from_dict=False)
                if articles:
                    await save_articles(articles)
                return articles
            
        except Exception as e:
            self.stderr.write(f"Error processing API category {category}: {e}")

        return []
    

    # Sitemap scraper


    async def _run_sitemap_optimized(self, site: dict, options: dict):
        sitemap_urls = site.get("sitemaps", [])[:options["feeds_per_site"]]
        all_articles = []

        for sitemap_url in sitemap_urls:
            try:
                scraper = SitemapScraper(sitemap_url)
                links = await scraper.fetch_articles(limit=options["articles_per_feed"])

                if links:
                    articles = await process_articles(links, site, from_dicts=False)
                    if articles:
                        await save_articles(articles)
                        all_articles.extend(articles)

            except Exception as e:
                self.stderr.write(f"Error processing sitemap {sitemap_url}: {e}")

        return all_articles


    
            



