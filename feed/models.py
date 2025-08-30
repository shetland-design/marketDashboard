from django.db import models

# Create your models here.
class NewsArticleModel(models.Model):
    source = models.CharField(max_length=100)
    title = models.CharField(unique=True, max_length=300)
    link = models.URLField(unique=True)
    published = models.DateField()
    full_content = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["published"]),
            models.Index(fields=["source"])
        ]

    def __str__(self):
        return f"{self.title} ({self.source})"
