import os
from django.shortcuts import render
from django.conf import settings

def get_pdf_files(directory):
    """Récupère tous les fichiers PDF d'un répertoire avec leurs métadonnées."""
    pdf_files = []
    if os.path.exists(directory):
        # Pour BKAM, vérifier le sous-dossier pdf_scraper
        if 'bkam.ma' in directory:
            directory = os.path.join(directory, 'pdf_scraper')
            if not os.path.exists(directory):
                return pdf_files

        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                file_path = os.path.join(directory, filename)
                title = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ')
                # Adapter le chemin du fichier en fonction de la structure
                site_name = os.path.basename(os.path.dirname(os.path.dirname(directory)))
                if 'bkam.ma' in directory:
                    subpath = os.path.join('pdf_downloads', os.path.basename(os.path.dirname(directory)), 'pdf_scraper', filename)
                else:
                    subpath = os.path.join('pdf_downloads', filename)
                
                pdf_files.append({
                    'title': title,
                    'file_path': f'/{site_name}/{subpath}',
                    'date': None
                })
    return sorted(pdf_files, key=lambda x: x['title'])

def home(request):
    return render(request, 'scraper/home.html')

def bkam_communiques(request):
    documents = get_pdf_files('bkam.ma/pdf_downloads/Communiques')
    context = {
        'site_name': 'BKAM',
        'site_icon': 'fas fa-bullhorn',
        'page_title': 'Communiqués de Bank Al-Maghrib',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def bkam_discours(request):
    documents = get_pdf_files('bkam.ma/pdf_downloads/Discours')
    context = {
        'site_name': 'BKAM',
        'site_icon': 'fas fa-microphone',
        'page_title': 'Discours de Bank Al-Maghrib',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def agriculture_documents(request):
    documents = get_pdf_files('agriculture.gov.ma/pdf_downloads')
    context = {
        'site_name': 'Agriculture.gov.ma',
        'site_icon': 'fas fa-leaf',
        'page_title': 'Documents du Ministère de l\'Agriculture',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def cese_documents(request):
    documents = get_pdf_files('cese.ma/pdf_downloads')
    context = {
        'site_name': 'CESE.ma',
        'site_icon': 'fas fa-landmark',
        'page_title': 'Documents du CESE',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def finances_documents(request):
    documents = get_pdf_files('finances.gov.ma/pdf_downloads')
    context = {
        'site_name': 'Finances.gov.ma',
        'site_icon': 'fas fa-coins',
        'page_title': 'Documents du Ministère des Finances',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)

def oecd_documents(request):
    documents = get_pdf_files('oecd.org/pdf_downloads')
    context = {
        'site_name': 'OECD.org',
        'site_icon': 'fas fa-globe',
        'page_title': 'Documents de l\'OCDE',
        'documents': documents
    }
    return render(request, 'scraper/documents.html', context)
