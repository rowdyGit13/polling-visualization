# Import Celery app to ensure it's loaded when Django starts
try:
    from .celery import app as celery_app
    __all__ = ['celery_app']
except ImportError:
    # Allow the app to work without Celery
    import warnings
    warnings.warn("Celery could not be imported - async tasks will not be available")
    __all__ = []
