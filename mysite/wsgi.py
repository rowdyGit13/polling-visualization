"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys

try:
    from django.core.wsgi import get_wsgi_application
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    
    application = get_wsgi_application()
    app = application
except Exception as e:
    # Write error to stderr for Vercel logs
    print(f"Error in WSGI application initialization: {str(e)}", file=sys.stderr)
    
    # Create a simple WSGI application that returns the error
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [f"Application initialization failed: {str(e)}".encode()]
    
    app = application
