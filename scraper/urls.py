from django.urls import path
from . import views

urlpatterns = [
    path('', views.WebsiteListView.as_view(), name='website-list'),
    path('website/add/', views.WebsiteCreateView.as_view(), name='website-create'),
    path('website/<int:pk>/', views.WebsiteDetailView.as_view(), name='website-detail'),
]