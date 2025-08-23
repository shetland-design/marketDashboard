from scraper import RssScraper, ArticleScraper


def test_science_daily():
    rss = RssScraper("https://www.sciencedaily.com/rss/top/science.xml", "ScienceDailyScience")

    articles = rss.fetch_articles(limit=3)

    for art in articles:
            print("=" * 80)
            print(f"Title: {art['title']}")
            print(f"Link: {art['link']}")
            print(f"Published: {art['published']}")
            print(f"Summary: {art['summary'][:150]}...")

            select = "div#story_text p"
            scraper = ArticleScraper(art["link"], select)
            full_text = scraper.article_content_2()

            if full_text:
                print("\nExtracted content preview:")
                print(full_text[-10:], "...\n")
            else:
                print("\n Could not extract content\n")