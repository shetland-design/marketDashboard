from scraper import api_scraper


def test_static():
    scraper = api_scraper.BackendApiScraper(
        url="https://thenextweb.com/deep-tech", 
        source="the_next_web",
        categories=[], 
        selectors={
            "container":"main.c-split__main",
            "articles": "article a"
    }
    )
    links = scraper.fetch_article_links(limit=5)

    print(links)

if __name__ == "__main__":
    test_static()