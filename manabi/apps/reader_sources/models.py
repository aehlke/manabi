from django.db import models


class ReaderSource(models.Model):
    source_url = models.URLField(max_length=700, unique=True)
    title = models.CharField(max_length=500)
    thumbnail_url = models.URLField(max_length=700, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(blank=True, null=True)
