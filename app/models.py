# import common
import datetime

# django
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _

# other
from model_utils import FieldTracker

# my
from app.mixins.state import StateMixin
from app import common


class BaseModel(models.Model):
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)
    update_date = models.DateTimeField(auto_now=True)

    class Meta(object):
        abstract = True


class Project(BaseModel):
    name = models.CharField(max_length=100)
    telegram_user = models.ForeignKey('TelegramUser', on_delete=models.CASCADE)

    # counts
    total_pomodoros = models.IntegerField(editable=False, default=0)
    total_rest = models.IntegerField(editable=False, default=0)

    class Meta(object):
        unique_together = ('telegram_user', 'name')

    def __str__(self):
        return self.name


class TelegramUser(StateMixin, BaseModel):
    USER_STATUSES = (
        ('active', 'Active'),
        ('banned', 'Banned'),
    )

    user_id = models.CharField(max_length=100, db_index=True)
    first_name = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    pomodoro_duration = models.DurationField(default=datetime.timedelta(minutes=25))
    pomodoro_rest = models.DurationField(default=datetime.timedelta(minutes=5))
    pomodoro_big_rest = models.DurationField(default=datetime.timedelta(minutes=15))
    pomodoro_session_count = models.IntegerField(default=4)
    current_project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, default=USER_STATUSES[0][0], db_index=True)

    def __str__(self):
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts)

    @property
    def is_admin(self):
        return self.user_id in settings.TELEGRAM_ADMIN_USERS

    @property
    def name(self):
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts)

    @property
    def pomodoro_minutes(self):
        return self.pomodoro_duration.seconds // 60

    @property
    def rest_minutes(self):
        return self.pomodoro_rest.seconds // 60

    @property
    def big_rest_minutes(self):
        return self.pomodoro_big_rest.seconds // 60


class PomodoroBase(BaseModel):

    class Meta(object):
        abstract = True

    STATUSES = [
        ('started', 'Started'),
        ('finished', 'Finished'),
        ('unfinished', 'Unfinished')
    ]
    start_date = models.DateTimeField(db_index=True)
    end_date = models.DateTimeField(db_index=True, null=True, blank=True)
    duration = models.DurationField(default=datetime.timedelta(minutes=25))
    status = models.CharField(choices=STATUSES, db_index=True, max_length=40, default=STATUSES[0][0])
    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE)

    task_id = models.CharField(null=True, blank=True, max_length=100)

    @property
    def real_duration(self):
        if not self.end_date:
            return None

        # strip microseconds
        return datetime.timedelta(seconds=(self.end_date - self.start_date).seconds)


class Pomodoro(PomodoroBase):
    tracker = FieldTracker()


class Rest(PomodoroBase):
    tracker = FieldTracker()


class Contact(BaseModel):
    CONTACT_STATUSSES = (
        ('new', 'New'),
        ('answered', 'Answered'),
        ('rejected', 'Rejected'),
        ('duplicate', 'Duplicate'),
    )

    message = models.TextField()
    telegram_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)

    answer = models.TextField(null=True, blank=True, verbose_name=_('Answer'))
    status = models.CharField(choices=CONTACT_STATUSSES, max_length=100, default=CONTACT_STATUSSES[0][0],
                              verbose_name=_('Status'))

    tracker = FieldTracker()

    class Meta(object):
        ordering = ['-create_date']


class MessageSender(BaseModel):
    SENDER_CATEGORY = (
        ('all', 'All'),
    )

    SENDER_STATUS = (
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    )

    category = models.CharField(choices=SENDER_CATEGORY, max_length=50, db_index=True, default=SENDER_CATEGORY[0][0],
                                verbose_name=_('Category'))
    status = models.CharField(choices=SENDER_STATUS, max_length=50, db_index=True, default=SENDER_STATUS[0][0],
                              verbose_name=_('Status'))

    title = models.CharField(max_length=512, verbose_name=_('Title'))
    message = models.TextField(verbose_name=_('Message'))

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_('Author'))


class Audio(BaseModel):
    CATEGORIES = (
        ('programming', 'Music for programming'),
    )
    audio = models.FileField(upload_to='audio')
    name = models.CharField(max_length=100)
    category = models.CharField(choices=CATEGORIES, max_length=100, db_index=True)

    audio_id = models.CharField(max_length=100, db_index=True)

    tracker = FieldTracker()


def decrease_total(sender, project):
    if sender == Pomodoro:
        project.total_pomodoros = models.F("total_pomodoros") - 1
    elif sender == Rest:
        project.total_rest = models.F("total_rest") - 1
    project.save()


def increase_total(sender, project):
    if sender == Pomodoro:
        project.total_pomodoros = models.F("total_pomodoros") + 1
    elif sender == Rest:
        project.total_rest = models.F("total_rest") + 1
    project.save()


@receiver(models.signals.post_save, sender=Rest)
@receiver(models.signals.post_save, sender=Pomodoro)
def add_project_pomodoro_count(sender, instance, created, **kwargs):
    if created:
        if instance.project:
            increase_total(sender, instance.project)
    else:
        if instance.tracker.has_changed('project_id'):
            old_project_id = instance.tracker.previous('project_id')
            if old_project_id:
                try:
                    old_project = Project.objects.get(id=old_project_id)
                    decrease_total(sender, old_project)
                except Project.DoesNotExist:
                    pass

            increase_total(sender, instance.project)


@receiver(models.signals.post_delete, sender=Rest)
@receiver(models.signals.post_delete, sender=Pomodoro)
def delete_project_pomodoro_count(sender, instance, **kwargs):
    try:
        project = instance.project
        decrease_total(sender, project)
    except Project.DoesNotExist:
        pass


@receiver(models.signals.post_save, sender=Contact)
def send_email_to_admin_question(sender, instance, created, **kwargs):
    if created:
        body = """
            Contact from user:

            Message: {c.message}
            Name: {c.telegram_user.name}
        """.format(c=instance)
        send_mail('Question from user', body, settings.SERVER_EMAIL, common.get_admin_emails())


@receiver(models.signals.post_save, sender=Contact)
def send_answer(sender, instance, created, **kwargs):
    if not created and instance.tracker.has_changed('answer') and instance.status == 'new':
        from bot.telegram import create_bot_from_user
        bot = create_bot_from_user(instance.telegram_user)
        message = _('Your feedback:\n{o.message}\n\nAnswer:\n{o.answer}').format(o=instance)
        bot.sender.sendMessage(message)

        instance.status = 'answered'
        instance.save()


@receiver(models.signals.post_save, sender=MessageSender)
def schedule_messenger(sender, instance, created, **kwargs):
    if created:
        from app.tasks import send_messages_task
        eta = timezone.now() + datetime.timedelta(seconds=5)
        send_messages_task.apply_async((instance.id, ), eta=eta)


@receiver(models.signals.post_save, sender=Audio)
def upload_file(sender, instance, created, **kwargs):
    if instance.tracker.has_changed('audio') and instance.audio:
        from app.tasks import upload_telegram_audio_task
        eta = timezone.now() + datetime.timedelta(seconds=5)
        upload_telegram_audio_task.apply_async((instance.id, ), eta=eta)
