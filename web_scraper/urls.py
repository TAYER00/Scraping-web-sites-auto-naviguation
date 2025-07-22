from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('scraper:home')),  # Redirection de la racine vers home avec namespace
    path('scraper/', include('scraper.urls')),  # Inclusion des URLs de l'app scraper
]

# Servir les fichiers statiques et PDF en développement
if settings.DEBUG:
    # Servir les fichiers statiques
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Servir les fichiers PDF de chaque site
    for site_dir in settings.STATICFILES_DIRS:
        site_path = f'/{site_dir.name}/'
        urlpatterns += [
            *static(site_path, document_root=site_dir, show_indexes=True),
        ]
