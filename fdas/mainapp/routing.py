from django.urls import re_path

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from mainapp import consumers

websocket_urlpatterns = [
    re_path(r'ws/positions/$', consumers.PositionsConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    # http->django views is added by default
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
