import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ririnBNI.BNI_ririn.settings')

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command

application = get_wsgi_application()

def handler(request, context):
    try:
        call_command('migrate', interactive=False)
        return {
            "statusCode": 200,
            "body": "Migration completed successfully!"
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Migration failed: {str(e)}"
        }
