# extractor/apps.py
from django.apps import AppConfig

class ExtractorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'extractor'  # Esto es importante