import sys
import os

# Point to your Django project directory (adjust if needed)
sys.path.append(os.path.join(os.path.dirname(__file__), "lostandfound"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lostandfound.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
