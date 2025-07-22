from django.contrib import admin
from .models import Website, ScrapedPDF

@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'created_at', 'pdf_count')
    search_fields = ('name', 'url')
    readonly_fields = ('created_at',)

    def pdf_count(self, obj):
        return obj.pdfs.count()
    pdf_count.short_description = 'Nombre de PDFs'

@admin.register(ScrapedPDF)
class ScrapedPDFAdmin(admin.ModelAdmin):
    list_display = ('title', 'website', 'downloaded_at')
    list_filter = ('website', 'downloaded_at')
    search_fields = ('title', 'url')
    readonly_fields = ('downloaded_at',)
