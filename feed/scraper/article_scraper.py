import httpx
from selectolax.parser import HTMLParser
import trafilatura as traf
from newspaper import Article
import json
from datetime import datetime
import re
from urllib.parse import urlparse
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleScraper:
    def __init__(self, url):
        self.url = url
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
                "Connection": "keep-alive",
            },
            timeout=30.0
        )
        self.html_content = None
        self.parser = None

    async def fetch_article_page(self):
        async with httpx.AsyncClient(
            headers=self.client.headers,
            timeout=self.client.timeout
        ) as client:
            try: 
                resp = await client.get(self.url)
                resp.raise_for_status()
                self.html_content = resp.text
                self.parser = HTMLParser(self.html_content)
                return self.html_content
            except httpx.RequestError as e:
                logger.error(f"Request failed for {self.url}: {e}")
            except httpx.HTTPStatusError as e:
                logger.error(f"Bad status {e.response.status_code} for {self.url}")
        return None

    async def extract_title_multiple_methods(self):
        """Extract title using multiple methods with fallbacks"""
        titles = []
        
        if not self.html_content:
            await self.fetch_article_page()
            
        if not self.parser:
            return None

        # Method 1: Meta property og:title
        og_title = self.parser.css_first('meta[property="og:title"]')
        if og_title and og_title.attributes.get('content'):
            titles.append(og_title.attributes['content'].strip())

        # Method 2: Meta name twitter:title
        twitter_title = self.parser.css_first('meta[name="twitter:title"]')
        if twitter_title and twitter_title.attributes.get('content'):
            titles.append(twitter_title.attributes['content'].strip())

        # Method 3: Regular title tag
        title_tag = self.parser.css_first('title')
        if title_tag and title_tag.text():
            titles.append(title_tag.text().strip())

        # Method 4: h1 tags (often contains the article title)
        h1_tags = self.parser.css('h1')
        for h1 in h1_tags:
            if h1.text():
                titles.append(h1.text().strip())

        # Method 5: JSON-LD structured data
        json_ld_title = self.extract_from_json_ld('headline')
        if json_ld_title:
            titles.append(json_ld_title)

        # Method 6: Article-specific selectors
        article_title_selectors = [
            'h1.article-title',
            'h1[data-testid="headline"]',
            '.headline',
            '.article-headline',
            '[data-testid="article-headline"]',
            'h1.entry-title'
        ]
        
        for selector in article_title_selectors:
            element = self.parser.css_first(selector)
            if element and element.text():
                titles.append(element.text().strip())

        # Clean and return the best title
        titles = [self.clean_title(title) for title in titles if title]
        titles = list(dict.fromkeys(titles))  # Remove duplicates while preserving order
        
        return titles[0] if titles else None

    async def extract_date_multiple_methods(self):
        """Extract publication date using multiple methods"""
        dates = []
        
        if not self.html_content:
            await self.fetch_article_page()
            
        if not self.parser:
            return None

        # Method 1: Meta property article:published_time
        article_published = self.parser.css_first('meta[property="article:published_time"]')
        if article_published and article_published.attributes.get('content'):
            dates.append(article_published.attributes['content'])

        # Method 2: Meta property og:published_time  
        og_published = self.parser.css_first('meta[property="og:published_time"]')
        if og_published and og_published.attributes.get('content'):
            dates.append(og_published.attributes['content'])

        # Method 3: Meta name publish_date
        publish_date = self.parser.css_first('meta[name="publish_date"]')
        if publish_date and publish_date.attributes.get('content'):
            dates.append(publish_date.attributes['content'])

        # Method 4: Time elements with datetime attribute
        time_elements = self.parser.css('time[datetime]')
        for time_elem in time_elements:
            datetime_attr = time_elem.attributes.get('datetime')
            if datetime_attr:
                dates.append(datetime_attr)

        # Method 5: JSON-LD structured data
        json_ld_date = self.extract_from_json_ld('datePublished')
        if json_ld_date:
            dates.append(json_ld_date)

        # Method 6: Date-specific selectors
        date_selectors = [
            '.publish-date',
            '.publication-date',
            '.article-date',
            '[data-testid="article-timestamp"]',
            '.timestamp',
            '.date-published'
        ]
        
        for selector in date_selectors:
            element = self.parser.css_first(selector)
            if element:
                if element.attributes.get('datetime'):
                    dates.append(element.attributes['datetime'])
                elif element.text():
                    dates.append(element.text().strip())

        # Method 7: Text pattern matching for dates
        if self.html_content:
            date_patterns = [
                r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
                r'\b\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',  # Month DD, YYYY
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, self.html_content, re.IGNORECASE)
                dates.extend(matches)

        # Clean and parse dates
        parsed_dates = []
        for date_str in dates:
            parsed_date = self.parse_date_string(date_str)
            if parsed_date:
                parsed_dates.append(parsed_date)

        return parsed_dates[0] if parsed_dates else None

    def extract_from_json_ld(self, field):
        """Extract data from JSON-LD structured data"""
        if not self.parser:
            return None
            
        json_scripts = self.parser.css('script[type="application/ld+json"]')
        
        for script in json_scripts:
            try:
                data = json.loads(script.text())
                
                # Handle arrays of JSON-LD objects
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and field in item:
                            return item[field]
                elif isinstance(data, dict):
                    # Direct field access
                    if field in data:
                        return data[field]
                    
                    # Check in @graph array
                    if '@graph' in data:
                        for item in data['@graph']:
                            if isinstance(item, dict) and field in item:
                                return item[field]
                                
            except (json.JSONDecodeError, KeyError):
                continue
                
        return None

    def parse_date_string(self, date_str):
        """Parse various date string formats"""
        if not date_str:
            return None
            
        # Clean the date string
        date_str = date_str.strip()
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%dT%H:%M:%S%z',      # ISO with timezone
            '%Y-%m-%dT%H:%M:%SZ',       # ISO UTC
            '%Y-%m-%dT%H:%M:%S',        # ISO without timezone
            '%Y-%m-%d %H:%M:%S',        # SQL datetime
            '%Y-%m-%d',                 # YYYY-MM-DD
            '%B %d, %Y',                # Month DD, YYYY
            '%b %d, %Y',                # Mon DD, YYYY
            '%d %B %Y',                 # DD Month YYYY
            '%d %b %Y',                 # DD Mon YYYY
            '%m/%d/%Y',                 # MM/DD/YYYY
            '%d/%m/%Y',                 # DD/MM/YYYY
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        return None

    def clean_title(self, title):
        """Clean and normalize title text"""
        if not title:
            return None
            
        # Remove common suffixes
        suffixes_to_remove = [
            ' - Fast Company',
            ' | Fast Company', 
            ' - CNN',
            ' | CNN',
            ' - BBC',
            ' | BBC',
            ' - Reuters',
            ' | Reuters'
        ]
        
        for suffix in suffixes_to_remove:
            if title.endswith(suffix):
                title = title[:-len(suffix)]
        
        return title.strip()

    async def newspaper_scraper(self):
        try:
        # Fetch HTML content if not already available
            if not self.html_content:
                await self.fetch_article_page()
        
        # Validate HTML content exists
            if not self.html_content:
                logging.warning(f"No HTML content available for URL: {self.url}")
                return None
        
        # Validate URL
            if not hasattr(self, 'url') or not self.url:
                logging.error("No URL provided for scraping")
                return None

            article = Article(self.url)
            
            try:
                # Method 1: Try as a method call
                if hasattr(article, 'article_html') and callable(article.article_html):
                    article.article_html(self.html_content)
                # Method 2: Try setting as property
                elif hasattr(article, 'article_html'):
                    article.article_html = self.html_content
                # Method 3: Try set_html method (newer versions)
                elif hasattr(article, 'set_html') and callable(article.set_html):
                    article.set_html(self.html_content)
                # Method 4: Try setting html property directly
                elif hasattr(article, 'html'):
                    article.html = self.html_content
                else:
                    logging.error("Unable to set HTML content on Article object")
                    return None
            except Exception as html_error:
                logging.error(f"Failed to set HTML content: {html_error}")
                return None

            def parse_article():
                article.download()
                article.parse()
                return article
            
            try:
                loop = asyncio.get_event_loop()
                article = await loop.run_in_executor(None, parse_article)
            except Exception as parse_error:
                logging.error(f"Failed to parse article: {parse_error}")
                return None


            if not article.title and not article.text:
                logging.warning(f"Failed to extract meaningful content from {self.url}")
                return None
            
            publish_date = None
            if article.publish_date:
                if isinstance(article.publish_date, datetime):
                    publish_date = article.publish_date.isoformat()
                else:
                    publish_date = str(article.publish_date)

            text_content = article.text.strip() if article.text else ""
            title = article.title.strip() if article.title else ""

            return {
                "title": title,
                "text": text_content,
                "authors": article.authors or [],
                "publish_date": publish_date
                }
        
        except ImportError as e:
            logging.error(f"newspaper3k library not available: {e}")
            return None
        except AttributeError as e:
            logging.error(f"Missing required attributes: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error scraping {getattr(self, 'url', 'unknown URL')}: {e}")
            return None
        

    async def trafilatura_scraper(self, is_json: bool = False):
        if not self.html_content:
            await self.fetch_article_page()  # fetch once if not done yet

        if not self.html_content:
            return None
            
        if is_json:
            result = traf.extract(
                self.html_content, 
                no_fallback=False,  # Allow fallback methods
                output_format='json',
                include_comments=False,
                include_tables=True
                    ) 
            return json.loads(result)
        else:
            return traf.extract(
                self.html_content,
                no_fallback=False,
                include_comments=False,
                include_tables=True
                    )
                    
            

    async def extract_comprehensive(self):
        """Extract article data using all available methods"""
        result = {
            'url': self.url,
            'title': None,
            'date': None,
            'text': None,
            'authors': None,
            'extraction_method': None
        }
        
        # Try multiple extraction methods
        methods = []
        
        # Method 1: Custom extraction
        try:
            title = await self.extract_title_multiple_methods()
            date = await self.extract_date_multiple_methods()
            if title or date:
                methods.append('custom_selectors')
                if title:
                    result['title'] = title
                if date:
                    result['date'] = date
        except Exception as e:
            logger.error(f"Custom extraction failed: {e}")

        # Method 2: Trafilatura with JSON
        try:
            traf_result = await self.trafilatura_scraper(is_json=True)
            if traf_result:
                methods.append('trafilatura')
                if not result['title'] and traf_result.get('title'):
                    result['title'] = traf_result['title']
                if not result['date'] and traf_result.get('date'):
                    result['date'] = traf_result['date']
                if not result['text'] and traf_result.get('text'):
                    result['text'] = traf_result['text']
                if not result['authors'] and traf_result.get('author'):
                    result['authors'] = [traf_result['author']] if isinstance(traf_result['author'], str) else traf_result['author']
        except Exception as e:
            logger.error(f"Trafilatura JSON extraction failed: {e}")

        # Method 3: Newspaper3k
        try:
            newspaper_result = await self.newspaper_scraper()
            if newspaper_result:
                methods.append('newspaper')
                if not result['title'] and newspaper_result.get('title'):
                    result['title'] = newspaper_result['title']
                if not result['date'] and newspaper_result.get('publish_date'):
                    result['date'] = newspaper_result['publish_date']
                if not result['text'] and newspaper_result.get('text'):
                    result['text'] = newspaper_result['text']
                if not result['authors'] and newspaper_result.get('authors'):
                    result['authors'] = newspaper_result['authors']
        except Exception as e:
            logger.error(f"Newspaper extraction failed: {e}")

        result['extraction_method'] = ', '.join(methods) if methods else 'none'
        
        # Clean up the client
        self.client.close()
        
        return result

# def main():
#     url = "https://www.infoworld.com/article/4030321/teradata-joins-snowflake-databricks-in-expanding-mcp-ecosystem.html"
    
#     scraper = ArticleScraper(url)
#     result = scraper.extract_comprehensive()
    
#     print("=== COMPREHENSIVE EXTRACTION RESULTS ===")
#     print(f"URL: {result['url']}")
#     print(f"Title: {result['title']}")
#     print(f"Date: {result['date']}")
#     print(f"Authors: {result['authors']}")
#     print(f"Extraction Method: {result['extraction_method']}")
#     print(f"Text Preview: {result['text'][:200] if result['text'] else 'None'}...")
#     print("\n" + "="*50)


# if __name__ == "__main__":
#     main()