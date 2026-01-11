"""Web routes module."""

from src.web.routes.main import main_bp
from src.web.routes.songs import songs_bp

__all__ = ['main_bp', 'songs_bp']
