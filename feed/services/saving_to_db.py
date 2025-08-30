from feed.models import NewsArticleModel
import logging

logger = logging.getLogger(__name__)

def save_article(data: dict) -> NewsArticleModel | None:
    try:
        if not data.get("link"):
            logger.warning("Skipping article: missing 'link'")
            return None

        obj, created = NewsArticleModel.objects.get_or_create(
            link=data["link"],
            defaults={k: v for k, v in data.items() if k != "link"}
        )
        return obj

    except Exception as e:
        logger.error(f"Failed to save article: {data.get('title', 'Unknown')} — {e}")
        return None
