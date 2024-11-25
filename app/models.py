# models.py

from django.db import models

class ServerDocument(models.Model):
    doc_id = models.CharField(max_length=255, unique=True, primary_key=True)
    content = models.JSONField(blank=True, null=True)  # Added content field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
