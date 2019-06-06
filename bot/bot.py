# common
import datetime
import logging

# django
from django.conf import settings
from django.utils import timezone

# other
from www.celery import app

# my
from bot import messages
from bot import helper
from app import common
from app.models import TelegramUser, Pomodoro, Project, Rest, Contact, Audio
from app.tasks import finish_rest, finish_pomodoro


class Bot(object):

    def __init__(self, current_user, sender, page_size=10):
        self.current_user = current_user
        self.sender = sender
        self.page_size = page_size

        if not self.current_user.current_project:
            project = Project(name='default', telegram_user=self.current_user)
            project.save()

            self.current_user.current_project = project
            self.current_user.save()

    def get_menu(self):
        return helper.get_menu(self.current_user)

    def handle_stats(self, period):
        if period == 'day':
            start = timezone.now().date()
            end = start + datetime.timedelta(days=1)
        elif period == 'month':
            tmp = timezone.now().date()
            start = tmp.replace(day=1)
            end = common.increment_month(start)
        elif period == 'week':
            tmp = timezone.now().date()
            start = tmp - datetime.timedelta(days=tmp.weekday())
            end = start + datetime.timedelta(days=7)
        else:
            self.sender.sendMessage(messages.bad_period_message, reply_markup=self.get_menu())
            return

        pomodoros = Pomodoro.objects.select_related('project').filter(telegram_user=self.current_user,
                                                                      start_date__gte=start,
                                                                      start_date__lt=end)

        projects = {}
        for pomodoro in pomodoros:
            if pomodoro.project_id not in projects:
                projects[pomodoro.project_id] = {
                    'period': period,
                    'count_finished': 0,
                    'count_unfinished': 0,
                    'count_in_progress': 0,
                    'count': 0,
                    'total_duration': datetime.timedelta(seconds=0),
                    'project': pomodoro.project,
                }
            stats = projects[pomodoro.project_id]

            if pomodoro.status == 'finished':
                stats['count_finished'] += 1
            elif pomodoro.status == 'unfinished':
                stats['count_unfinished'] += 1
            else:
                stats['count_in_progress'] += 1

            if pomodoro.real_duration:
                stats['total_duration'] += pomodoro.real_duration
            stats['count'] += 1

        if projects:
            for data in projects.values():
                self.sender.sendMessage(messages.stats_message.format(**data), reply_markup=self.get_menu())
        else:
            self.sender.sendMessage(messages.no_stats_message, reply_markup=self.get_menu())

    def stop_activities(self):
        stop_pomodoro = False
        stop_rest = False

        current_pomodoro_id = self.current_user.get_state('current_pomodoro_id')
        if current_pomodoro_id:
            try:
                current_pomodoro = Pomodoro.objects.get(id=current_pomodoro_id)
                current_pomodoro.status = 'unfinished'
                current_pomodoro.end_date = timezone.now()
                current_pomodoro.save()

                if current_pomodoro.task_id:
                    try:
                        app.control.revoke(current_pomodoro.task_id)
                    except Exception as e:
                        logging.exception('Revoking current pomodoro task faield {}'.format(str(e)))

                stop_pomodoro = True
            except Pomodoro.DoesNotExist:
                pass
            finally:
                self.current_user.remove_state('current_pomodoro_id')

        current_rest_id = self.current_user.get_state('current_rest_id')
        if current_rest_id:
            try:
                current_rest = Rest.objects.get(id=current_rest_id)
                current_rest.status = 'unfinished'
                current_rest.end_date = timezone.now()
                current_rest.save()

                if current_rest.task_id:
                    try:
                        app.control.revoke(current_rest.task_id)
                    except Exception as e:
                        logging.exception('Revoking current pomodoro task faield {}'.format(str(e)))

                stop_rest = True
            except Pomodoro.DoesNotExist:
                pass
            finally:
                self.current_user.remove_state('current_rest_id')

        return stop_pomodoro, stop_rest

    def handle_pomodoro_run(self):
        current_pomodoro_id = self.current_user.get_state('current_pomodoro_id')
        if current_pomodoro_id:
            self.sender.sendMessage(messages.pomodoro_in_progress_message, reply_markup=self.get_menu())
            return

        self.stop_activities()

        pomodoro = Pomodoro()
        pomodoro.start_date = timezone.now()
        pomodoro.telegram_user = self.current_user
        pomodoro.project = self.current_user.current_project
        pomodoro.duration = self.current_user.pomodoro_duration
        pomodoro.save()

        countdown = 10 if settings.SERVER == 'dev' else self.current_user.pomodoro_duration.seconds
        eta = timezone.now() + datetime.timedelta(seconds=countdown)
        result = finish_pomodoro.apply_async(args=(self.current_user.id, pomodoro.id), eta=eta)

        pomodoro.task_id = result.id
        pomodoro.save()

        self.current_user.set_state('current_pomodoro_id', pomodoro.id)

        self.sender.sendMessage(messages.pomodoro_started_message, reply_markup=self.get_menu())

        audio = Audio.objects.exclude(audio_id__isnull=True).order_by('?').first()
        if audio:
            self.sender.sendAudio(audio.audio_id, audio.get_category_display())

    def handle_start_rest(self):
        stop_pomodoro, _ = self.stop_activities()

        if stop_pomodoro:
            self.sender.sendMessage(messages.pomodoro_stopped_message, reply_markup=self.get_menu())

        rest = Rest()
        rest.start_date = timezone.now()
        rest.telegram_user = self.current_user
        rest.project = self.current_user.current_project
        rest.duration = self.current_user.pomodoro_rest
        rest.save()

        countdown = 10 if settings.SERVER == 'dev' else self.current_user.pomodoro_rest.seconds
        eta = timezone.now() + datetime.timedelta(seconds=countdown)
        result = finish_rest.apply_async(args=(self.current_user.id, rest.id), eta=eta)

        rest.task_id = result.id
        rest.save()

        self.current_user.set_state('current_rest_id', rest.id)

        self.sender.sendMessage(messages.pomodoro_rest_started_message, reply_markup=self.get_menu())

    def handle_pomodoro_stop(self):
        current_pomodoro_id = self.current_user.get_state('current_pomodoro_id')
        if not current_pomodoro_id:
            self.sender.sendMessage(messages.pomodoro_no_message, reply_markup=self.get_menu())
            return

        self.stop_activities()

        self.sender.sendMessage(messages.pomodoro_stopped_message, reply_markup=self.get_menu())

    def handle_rest_stop(self):
        current_pomodoro_id = self.current_user.get_state('current_pomodoro_id')
        if current_pomodoro_id:
            self.sender.sendMessage(messages.pomodoro_in_progress_message, reply_markup=self.get_menu())
            return

        self.stop_activities()

        self.sender.sendMessage(messages.pomodoro_rest_stopped_message, reply_markup=self.get_menu())

    def on_chat_message(self, message):
        if not message:
            return

        self.current_user = TelegramUser.objects.get(id=self.current_user.id)

        if self.current_user.status != 'active':
            self.current_user.status = 'active'
            self.current_user.save()

        try:
            current_state = self.current_user.get_state_machine()

            if message == helper.BACK_TEXT and current_state:
                self.current_user.pop_state_machine()
                self.sender.sendMessage(messages.empty_command_message, reply_markup=self.get_menu())
            elif current_state:
                if message == helper.ADMIN_STATS_TEXT:
                    parts = []

                    data = {
                        'count': TelegramUser.objects.count(),
                        'model': 'users',
                    }
                    parts.append(messages.admin_count_message.format(**data))

                    data = {
                        'count': Pomodoro.objects.count(),
                        'model': 'pomodoros',
                    }
                    parts.append(messages.admin_count_message.format(**data))

                    data = {
                        'count': Rest.objects.count(),
                        'model': 'rest',
                    }
                    parts.append(messages.admin_count_message.format(**data))

                    self.sender.sendMessage('\n'.join(parts), reply_markup=self.get_menu())
                elif message == helper.ADMIN_ACTIVE_TEXT:
                    data = {
                        'active_pomodoros': Pomodoro.objects.filter(status='started').count(),
                        'active_rests': Rest.objects.filter(status='started').count(),
                    }
                    self.sender.sendMessage(messages.admin_count_active.format(**data),
                                                  reply_markup=self.get_menu())
                elif message == helper.STATS_DAY_TEXT:
                    self.handle_stats('day')
                elif message == helper.STATS_WEEK_TEXT:
                    self.handle_stats('week')
                elif message == helper.STATS_MONTH_TEXT:
                    self.handle_stats('month')
                elif current_state == 'projects':
                    if message.startswith(helper.SET_PROJECT_TEXT):
                        name = message[len(helper.SET_PROJECT_TEXT):].strip(' ☑')
                        project, created = Project.objects.get_or_create(telegram_user=self.current_user, name=name)
                        self.current_user.current_project = project
                        self.current_user.save()

                        self.current_user.pop_state_machine()

                        self.sender.sendMessage(messages.project_set_message.format(project=project),
                                                      reply_markup=self.get_menu())
                    elif message == helper.NEW_PROJECT_TEXT:
                        self.current_user.push_state_machine('new_project')
                        self.sender.sendMessage(messages.new_project_message, reply_markup=self.get_menu())
                    else:
                        self.sender.sendMessage(messages.bad_command_message, reply_markup=self.get_menu())
                elif current_state == 'new_project':
                    project, created = Project.objects.get_or_create(telegram_user=self.current_user, name=message)
                    self.current_user.current_project = project
                    self.current_user.save()

                    self.current_user.clear_state_machine()

                    self.sender.sendMessage(messages.project_set_message.format(project=project),
                                                  reply_markup=self.get_menu())
                elif current_state == 'contact':
                    contact = Contact()
                    contact.message = message
                    contact.telegram_user = self.current_user
                    contact.save()

                    self.current_user.pop_state_machine()
                    self.sender.sendMessage(messages.contact_us_sent, reply_markup=self.get_menu())
                elif current_state == 'settings':
                    if message.startswith(helper.SETTINGS_POMODORO_LENGTH):
                        self.current_user.push_state_machine('settings_pomodoro_length')
                        self.sender.sendMessage(messages.settings_pomodoro_message.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                    elif message.startswith(helper.SETTINGS_REST_LENGTH):
                        self.current_user.push_state_machine('settings_rest_length')
                        self.sender.sendMessage(messages.settings_rest_message.format(u=self.current_user),
                            reply_markup=self.get_menu())
                    elif message.startswith(helper.SETTINGS_BIG_REST_LENGTH):
                        self.current_user.push_state_machine('settings_big_rest_length')
                        self.sender.sendMessage(messages.settings_big_rest_message.format(u=self.current_user),
                            reply_markup=self.get_menu())
                    elif message.startswith(helper.SETTINGS_SET_POMODORO_COUNT):
                        self.current_user.push_state_machine('settings_session_count')
                        self.sender.sendMessage(messages.settings_session_count_message.format(u=self.current_user),
                            reply_markup=self.get_menu())
                    else:
                        self.sender.sendMessage(messages.bad_command_message, reply_markup=self.get_menu())
                elif current_state == 'settings_pomodoro_length':
                    try:
                        minutes = int(message)
                        if minutes < 1 or minutes > 60:
                            raise ValueError('Not in range')

                        self.current_user.pop_state_machine()

                        self.current_user.pomodoro_duration = datetime.timedelta(seconds=minutes * 60)
                        self.current_user.save()

                        self.sender.sendMessage(messages.settings_pomodoro_set_message.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                    except (TypeError, ValueError):
                        self.sender.sendMessage(messages.settings_error_minutes.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                elif current_state == 'settings_rest_length':
                    try:
                        minutes = int(message)
                        if minutes < 1 or minutes > 60:
                            raise ValueError('Not in range')

                        self.current_user.pop_state_machine()

                        self.current_user.pomodoro_rest = datetime.timedelta(seconds=minutes * 60)
                        self.current_user.save()

                        self.sender.sendMessage(messages.settings_rest_set_message.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                    except (TypeError, ValueError):
                        self.sender.sendMessage(messages.settings_error_minutes.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                elif current_state == 'settings_big_rest_length':
                    try:
                        minutes = int(message)
                        if minutes < 1 or minutes > 60:
                            raise ValueError('Not in range')

                        self.current_user.pop_state_machine()

                        self.current_user.pomodoro_big_rest = datetime.timedelta(seconds=minutes * 60)
                        self.current_user.save()

                        self.sender.sendMessage(messages.settings_big_rest_set_message.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                    except (TypeError, ValueError):
                        self.sender.sendMessage(messages.settings_error_minutes.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                elif current_state == 'settings_session_count':
                    try:
                        count = int(message)
                        if count < 1 or count > 60:
                            raise ValueError('Not in range')

                        self.current_user.pop_state_machine()

                        self.current_user.pomodoro_session_count = count
                        self.current_user.save()

                        self.sender.sendMessage(messages.settings_session_count_set_message.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                    except (TypeError, ValueError):
                        self.sender.sendMessage(messages.settings_error_session.format(u=self.current_user),
                                                      reply_markup=self.get_menu())
                else:
                    self.current_user.clear_state_machine()
                    self.sender.sendMessage(messages.bad_command_message, reply_markup=self.get_menu())
            else:
                if message in ('/start', '/help', helper.HELP_TEXT):
                    self.sender.sendMessage(messages.start_message, reply_markup=self.get_menu())
                elif message == helper.START_REST_TEXT:
                    self.handle_start_rest()
                elif message == helper.STOP_REST_TEXT:
                    self.handle_rest_stop()
                elif message == helper.START_TEXT:
                    self.handle_pomodoro_run()
                elif message == helper.STOP_TEXT:
                    self.handle_pomodoro_stop()
                elif message == helper.STATS_TEXT:
                    self.current_user.push_state_machine('stats')
                    self.sender.sendMessage(messages.stats_select_message, reply_markup=self.get_menu())
                elif message in [helper.CONTACT_US_TEXT, '/contact']:
                    self.current_user.push_state_machine('contact')
                    self.sender.sendMessage(messages.contact_us_message, reply_markup=self.get_menu())
                elif message == helper.ADMIN_TEXT and self.current_user.is_admin:
                    self.current_user.push_state_machine('admin')
                    self.sender.sendMessage(messages.admin_message, reply_markup=self.get_menu())
                elif message.startswith(helper.PROJECTS_TEXT):
                    self.current_user.push_state_machine('projects')
                    self.sender.sendMessage(messages.list_projects_message, reply_markup=self.get_menu())
                elif message == helper.SETTINGS_TEXT:
                    self.current_user.push_state_machine('settings')
                    self.sender.sendMessage(messages.settings_message, reply_markup=self.get_menu())
                else:
                    self.sender.sendMessage(messages.bad_command_message, reply_markup=self.get_menu())
        except Exception as e:
            try:
                self.sender.sendMessage('Internal error', reply_markup=self.get_menu())

                if settings.SERVER == 'dev':
                    logging.exception('Unexpected exception')
            except Exception as e:
                logging.exception('Unexpected exception while other exception')

    def on_callback(self, data):
        pass