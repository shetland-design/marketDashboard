def reuters_parser(data):
    articles = []
    for item in data.get("result", {}).get("articles", []):
        articles.append({
            "title": item.get("title"),
            "link": f"http://www.reuters.com{item.get("canonical_url")}",
            "summary": item.get("description"),
            "published": item.get("published_time")
        })
    return articles