# src/shelf/__init__.py
__version__ = "0.1.0"

from .shelf_feed_generator import ShelfError, ShelfFeedGenerator

print("I'm in danger!!!")

__all__ = ["__version__", ShelfFeedGenerator, ShelfError]
