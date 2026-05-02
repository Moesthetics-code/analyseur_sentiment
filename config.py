import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sentiment-app-secret-2024')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max upload
    UPLOAD_EXTENSIONS = {'.txt'}
    DEFAULT_LANGUAGE = 'fr'
