# common
import json
import logging

# django
from django.conf import settings
from django.views import generic
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

# other
import telepot

# my
from bot.sender import Sender
from bot.bot import Bot
from app.models import TelegramUser


def get_telegram_from_seed(message):
    chat = message['chat']
    current_user, _ = TelegramUser.objects.get_or_create(user_id=chat['id'])

    need_save = False
    first_name = chat.get('first_name')
    last_name = chat.get('last_name')

    if first_name != current_user.first_name:
        current_user.first_name = first_name
        need_save = True

    if last_name != current_user.last_name:
        current_user.last_name = last_name
        need_save = True

    if need_save:
        current_user.save()

    return current_user


class TelegramWebhook(generic.View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, token):
        assert token == settings.TELEGRAM_BOT_TOKEN

        setup_telegram_webhook()

    def post(self, request, token):

        try:
            raw = request.body.decode('utf8')
            logging.debug('Telegram raw data %s' % raw)
            update = json.loads(raw)
            if 'message' in update:
                data = message = update['message']
            elif 'callback_query' in update:
                data = update['callback_query']
                message = data['message']
            else:
                logging.error('Can not recognize update {}', update)
                raise TypeError('Not supported')

            current_user = get_telegram_from_seed(message)
            sender = Sender('telegram', current_user.user_id)
            bot = Bot(current_user, sender)
        except (TypeError, ValueError) as e:
            logging.exception("Can not decode message")
            return HttpResponse('Error')

        if token != settings.TELEGRAM_BOT_TOKEN:
            sender = Sender('telegram', current_user.user_id)
            sender.sendMessage('Our bot migrated to @{}'.format(settings.TELEGRAM_BOT_NAME), token=token)
            return HttpResponse('ok')

        try:
            flavor = telepot.flavor(data)
            if flavor == 'chat':
                text = message.get('text', '') or message.get('contact', {}).get('phone_number')
                if not text:
                    return HttpResponse('ok')

                bot.on_chat_message(text)
            elif flavor == 'callback_query':
                msg_id = (data['from']['id'], data['message']['message_id'])
                query_id, from_id, query_data = telepot.glance(data, flavor='callback_query')
                sender.msg_id = msg_id
                sender.query_id = query_id

                data = json.loads(query_data) if query_data else None
                if not data:
                    return HttpResponse('ok')

                bot.on_callback(data)
        except Exception:
            logging.exception('Error on handling bot message')
            try:
                sender.sendMessage('❌❌❌❌❌ Internal error', reply_markup=bot.get_menu())
            except Exception:
                logging.exception('Error on handling bot message error')

        return HttpResponse('ok')


def setup_telegram_webhook():
    bot = telepot.Bot(settings.TELEGRAM_BOT_TOKEN)
    url = settings.TUNNEL_URL + reverse('telegram_webhook', kwargs={'token': settings.TELEGRAM_BOT_TOKEN})
    bot.setWebhook(url)


def create_bot_from_user(bot_user, request=None):
    sender = Sender('telegram', bot_user.user_id)
    bot = Bot(bot_user, sender, request)
    return bot
