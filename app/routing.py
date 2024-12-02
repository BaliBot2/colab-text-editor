from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/editor/(?P<doc_id>[^/]+)/$', consumers.EditorConsumer.as_asgi()),
    ]
