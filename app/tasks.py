# common
import logging

# other
from post_office import mail
from www.celery import app
from django.core.management import call_command
from admin_logs.decorators import log
import telepot

# django
from django.conf import settings
from django.utils import timezone

# my
from app.models import Pomodoro, Rest, TelegramUser, MessageSender, Audio
from bot import helper
from bot import messages


@app.task(ignore_result=True)
def send_regular_emails_task():
    mail.send_queued()


@app.task(ignore_result=True)
def finish_pomodoro(user_id, pomodoro_id):
    logging.debug('Finish pomodoro user %s, pomodoro %s', user_id, pomodoro_id)

    try:
        telegram_user = TelegramUser.objects.get(id=user_id)
    except TelegramUser.DoesNotExist:
        return

    current_pomodoro_id = telegram_user.get_state('current_pomodoro_id')
    if current_pomodoro_id != pomodoro_id:
        return

    try:
        current_pomodoro = Pomodoro.objects.get(id=current_pomodoro_id)
        current_pomodoro.status = 'finished'
        current_pomodoro.end_date = timezone.now()
        current_pomodoro.save()

        telegram_user.remove_state('current_pomodoro_id')

        # first pomodoro? ask user to provide feed back
        options = telegram_user.get_state('options') or []
        if 'first_pomodoro' not in options:
            options.append('first_pomodoro')
            telegram_user.set_state('options', options)
            helper.send_message_to_user(telegram_user, messages.first_pomodoro_message)

        helper.send_message_to_user(telegram_user, messages.pomodoro_ended_message)
    except Pomodoro.DoesNotExist:
        pass


@app.task(ignore_result=True)
def finish_rest(user_id, rest_id):
    logging.debug('Finish rest user %s, rest %s', user_id, rest_id)

    try:
        telegram_user = TelegramUser.objects.get(id=user_id)
    except TelegramUser.DoesNotExist:
        return

    current_rest_id = telegram_user.get_state('current_rest_id')
    if current_rest_id != rest_id:
        return

    try:
        current_rest = Rest.objects.get(id=current_rest_id)
        current_rest.status = 'finished'
        current_rest.end_date = timezone.now()
        current_rest.save()

        telegram_user.remove_state('current_rest_id')

        helper.send_message_to_user(telegram_user, messages.pomodoro_rest_ended_message)
    except Rest.DoesNotExist:
        pass


@app.task(ignore_result=True)
def send_messages_task(sender_id):
    logging.debug("Send message %s" % sender_id)

    sender = MessageSender.objects.get(id=sender_id)

    send_users = []

    if sender.category == 'all':
        query = TelegramUser.objects.all()
    else:
        raise Exception('Wring category {}'.format(sender.category))

    for telegram_user in query:
        if telegram_user.id in send_users:
            continue
        send_users.append(telegram_user.id)

        try:
            helper.send_message_to_user(telegram_user, sender.message)
        except Exception:
            logging.exception("Can not send message for user %s" % telegram_user.id)

    sender.status = 'sent'
    sender.save()


@app.task(ignore_result=True)
def upload_telegram_audio_task(audio_id):
    try:
        audio = Audio.objects.get(id=audio_id)

        bot = telepot.Bot(settings.TELEGRAM_BOT_TOKEN)

        if not audio.audio:
            return

        with open(audio.audio.path, 'rb') as audio_file:
            res = bot.sendAudio(settings.TELEGRAM_ADMIN_USERS[0], (audio.name, audio_file))

            audio.audio_id = res['audio']['file_id']
            audio.save()
    except Audio.DoesNotExist:
        pass


@app.task(ignore_result=True)
@log('Run backup')
def backup_task():
    call_command('dbbackup', clean=True)
    call_command('mediabackup', clean=True)
