# django
from django.conf import settings

# other
import telepot
from bot.sender import Button, Markup, Sender

# my
from app import common


START_TEXT = '⏲Start pomodoro'
STOP_TEXT = '⏰Stop pomodoro'
START_REST_TEXT = '☕Start rest'
STOP_REST_TEXT = '⏰Stop rest'

STATS_TEXT = 'ℹ️ Stats'
STATS_DAY_TEXT = '♭Day'
STATS_WEEK_TEXT = '♮Week'
STATS_MONTH_TEXT = '♯Month'

HELP_TEXT = '❓Help'
CONTACT_US_TEXT = '📞Contact us'
PROJECTS_TEXT = '☰Projects'
NEW_PROJECT_TEXT = '🆕New project'
SET_PROJECT_TEXT = 'Set project:'
BACK_TEXT = '🔙Back'

ADMIN_TEXT = '☢Admin'
ADMIN_STATS_TEXT = 'Admin Stats'
ADMIN_ACTIVE_TEXT = 'Admin Active'
SETTINGS_TEXT = '⚒Settings'
SETTINGS_POMODORO_LENGTH = 'Set pomodoro length: '
SETTINGS_REST_LENGTH = 'Set rest length: '
SETTINGS_BIG_REST_LENGTH = 'Set big rest length: '
SETTINGS_SET_POMODORO_COUNT = 'Set pomodoro session count: '

BACK_ROW = [
    Button(text=BACK_TEXT),
]


def get_menu(telegram_user):
    keyboard = []
    current_state = telegram_user.get_state_machine()
    current_pomodoro = telegram_user.get_state('current_pomodoro_id')
    current_rest = telegram_user.get_state('current_rest_id')

    if telegram_user.is_admin and current_state == 'admin':
        admin_row = [
            Button(text=ADMIN_STATS_TEXT),
            Button(text=ADMIN_ACTIVE_TEXT),
        ]
        keyboard = [
            admin_row,
            BACK_ROW,
        ]
    elif current_state == 'stats':
        stats_row = [
            Button(text=STATS_DAY_TEXT),
            Button(text=STATS_WEEK_TEXT),
            Button(text=STATS_MONTH_TEXT),
        ]

        keyboard = [
            stats_row,
            BACK_ROW,
        ]
    elif current_state == 'contact':
        keyboard = [
            BACK_ROW,
        ]
    elif current_state == 'projects':
        projects = telegram_user.project_set.order_by('-total_pomodoros')

        for chunk in common.chunker(projects, 2):
            projects_row = []
            for project in chunk:
                text = SET_PROJECT_TEXT + ' ' + project.name
                if project.id == telegram_user.current_project.id:
                    text += ' ☑'
                projects_row.append(Button(text=text))
            keyboard.append(projects_row)

        keyboard.append([
            Button(text=NEW_PROJECT_TEXT),
            Button(text=BACK_TEXT),
        ])
    elif current_state == 'new_project':
        keyboard.append(BACK_ROW)
    elif current_state == 'settings':
        keyboard.append([
            Button(text=SETTINGS_POMODORO_LENGTH + str(telegram_user.pomodoro_minutes)),
        ])
        keyboard.append([
            Button(text=SETTINGS_REST_LENGTH + str(telegram_user.rest_minutes)),
        ])
        keyboard.append([
            Button(text=SETTINGS_BIG_REST_LENGTH + str(telegram_user.big_rest_minutes)),
        ])
        keyboard.append([
            Button(text=SETTINGS_SET_POMODORO_COUNT + str(telegram_user.pomodoro_session_count)),
        ])
        keyboard.append(BACK_ROW)
    elif current_state == 'settings_pomodoro_length':
        keyboard.append(BACK_ROW)
    elif current_state == 'settings_rest_length':
        keyboard.append(BACK_ROW)
    elif current_state == 'settings_big_rest_length':
        keyboard.append(BACK_ROW)
    elif current_state == 'settings_session_count':
        keyboard.append(BACK_ROW)
    else:
        first_row = []
        if current_pomodoro:
            first_row.append(Button(text=STOP_TEXT))
            first_row.append(Button(text=START_REST_TEXT))
        else:
            first_row.append(Button(text=START_TEXT))

            if current_rest:
                first_row.append(Button(text=STOP_REST_TEXT))
            else:
                first_row.append(Button(text=START_REST_TEXT))

        second_row = [
            Button(text=PROJECTS_TEXT + ': ' + telegram_user.current_project.name),
            Button(text=STATS_TEXT),
        ]

        third_row = [
            Button(text=HELP_TEXT),
            Button(text=CONTACT_US_TEXT),
            Button(text=SETTINGS_TEXT),
        ]
        keyboard.append(first_row)
        keyboard.append(second_row)
        keyboard.append(third_row)

        if telegram_user.is_admin:
            admin_row = []
            admin_row.append(Button(text=ADMIN_TEXT))
            keyboard.append(admin_row)

    return Markup(buttons=keyboard) if keyboard else None


def send_message_to_user(telegram_user, message):
    try:
        sender = Sender('telegram', telegram_user.user_id)
        sender.sendMessage(message, reply_markup=get_menu(telegram_user))
    except (telepot.exception.BotWasBlockedError, telepot.exception.BotWasBlockedError):
        telegram_user.status = 'banned'
        telegram_user.save()
