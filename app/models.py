from django.db import models

class ServerDocument(models.Model):
    doc_id = models.CharField(max_length=255, unique=True, primary_key=True)  # Primary key
    content = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
