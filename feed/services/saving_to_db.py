from feed.models import NewsArticleModel
import logging
import asyncio
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


@sync_to_async
def save_articles(data: list) -> NewsArticleModel | None:
    results = {
        'saved': [],
        'failed': [],
        'total_attempted': len(data)
    }

    for article in data:
        try:
            if not article.get("link"):
                results['failed'].append({
                    'data': article,
                    'error': "Missing link"
                })
                continue

            obj, created = NewsArticleModel.objects.get_or_create(
                link=article["link"],
                defaults={k: v for k, v in article.items() if k != "link"}
            )
            results['saved'].append({
                'object': obj,
                'created': created
            })

        except Exception as e:
            logger.error(f"Failed to save article: {article.get('title', 'Unknown')} — {e}")
            results['failed'].append({
                'data': article,
                'error': str(e)
            })
    
    logger.info(f"Bulk save completed: {len(results['saved'])} saved, {len(results['failed'])} failed")
    return results
