from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

from main.consumers import ChatConsumer
application = ProtocolTypeRouter({
    # WebSocket chat handler
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r'^ws/chat/(?P<mode>(vk|tm))/$', ChatConsumer),
        ])
    ),
})
