from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Website, ScrapedPDF
from .crawler import start_crawling
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

class WebsiteListView(ListView):
    model = Website
    template_name = 'scraper/website_list.html'
    context_object_name = 'websites'

class WebsiteDetailView(DetailView):
    model = Website
    template_name = 'scraper/website_detail.html'
    context_object_name = 'website'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pdfs'] = self.object.pdfs.all().order_by('-downloaded_at')
        return context

class WebsiteCreateView(CreateView):
    model = Website
    template_name = 'scraper/website_form.html'
    fields = ['name', 'url']
    success_url = reverse_lazy('website-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            # Start crawling in the background
            pdf_links = start_crawling(self.object.url, self.object.name)
            messages.success(self.request, f'Successfully started crawling {self.object.name}. Found {len(pdf_links)} PDFs.')
        except Exception as e:
            messages.error(self.request, f'Error starting crawler: {str(e)}')
        return response
