# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('editor/<str:doc_id>/', views.load_document, name='load_document'),
    path('new/', views.new_document, name='new_document'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('share/<str:doc_id>/', views.share_document, name='share_document'),
    path('shared-users/<str:doc_id>/', views.get_shared_users, name='get_shared_users'),
    path('remove-access/<int:access_id>/', views.remove_access, name='remove_access'),
    path('delete/<str:doc_id>/', views.delete_document, name='delete_document'),
]

