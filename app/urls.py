from django.conf.urls import url
from app.views import home
from bot.telegram import TelegramWebhook


urlpatterns = [
    url(r'^$', home),
    url(r'^telegram/(?P<token>[0-9a-zA-Z:_-]+)/?$', TelegramWebhook.as_view(), name='telegram_webhook'),
]
