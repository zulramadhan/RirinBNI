import os
import sys

# Start from root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BNI_ririn.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application
