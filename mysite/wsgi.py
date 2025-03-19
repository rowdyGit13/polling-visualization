"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
import traceback

try:
    from django.core.wsgi import get_wsgi_application
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    
    application = get_wsgi_application()
    app = application
except Exception as e:
    # Print full traceback
    error_details = traceback.format_exc()
    print(f"Error in WSGI application initialization:\n{error_details}", file=sys.stderr)
    
    # Create a simple WSGI application that returns the error
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        error_message = f"Application initialization failed:\n{error_details}"
        return [error_message.encode()]
    
    app = application
