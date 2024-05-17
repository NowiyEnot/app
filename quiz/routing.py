from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/quiz/(?P<room_token>\w+)/$', consumers.QuizConsumer.as_asgi()),
]