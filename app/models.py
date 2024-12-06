# models.py
from django.db import models
from django.contrib.auth.models import User

class ServerDocument(models.Model):
    doc_id = models.CharField(max_length=255, unique=True, primary_key=True)
    title = models.CharField(max_length=255, default="Untitled Document")  
    content = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    visibility = models.CharField(
        max_length=10,
        choices=[('PRIVATE', 'Private'), ('PUBLIC', 'Public')],
        default='PRIVATE'
    )

class DocumentAccess(models.Model):
    document = models.ForeignKey(ServerDocument, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_type = models.CharField(
        max_length=6,
        choices=[('EDITOR', 'Editor'), ('VIEWER', 'Viewer')],
        default='VIEWER'
    )
    created_at = models.DateTimeField(auto_now_add=True)