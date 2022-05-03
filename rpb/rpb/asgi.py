"""
ASGI config for rpb project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import recommender.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rpb.settings')

application = ProtocolTypeRouter({
    'http':get_asgi_application(),
    'websocket':URLRouter(
        recommender.routing.websocket_urlpatterns,

    )
}
)
