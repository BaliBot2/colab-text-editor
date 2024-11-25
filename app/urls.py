from django.shortcuts import redirect
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('editor/<str:doc_id>/', views.load_document, name='load_document'),
    path('new/', views.new_document, name='new_document'),

    # TODO add a path for a regular expression corresonding to a document ID
    # TODO add a path for 404 document not found
]
