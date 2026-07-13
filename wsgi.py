"""
WSGI entrypoint for production deployment.
Loads the application factory and exposes the app object.
"""
import os
from backend.app import create_app
from backend.config import ProductionConfig, DevelopmentConfig

env = os.getenv("FLASK_ENV", "production")
config = ProductionConfig if env == "production" else DevelopmentConfig
app = create_app(config)
