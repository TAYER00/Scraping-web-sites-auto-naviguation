from django.urls import path
from . import views

app_name = 'scraper'

urlpatterns = [
    path('', views.home, name='home'),
    path('bkam/communiques/', views.bkam_communiques, name='bkam_communiques'),
    path('bkam/discours/', views.bkam_discours, name='bkam_discours'),
    path('agriculture/', views.agriculture_documents, name='agriculture_documents'),
    path('cese/', views.cese_documents, name='cese_documents'),
    path('finances/', views.finances_documents, name='finances_documents'),
    path('oecd/', views.oecd_documents, name='oecd_documents'),
]