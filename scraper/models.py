from django.db import models

class Website(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ScrapedPDF(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='pdfs')
    title = models.CharField(max_length=500)
    url = models.URLField()
    file_path = models.CharField(max_length=500)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
