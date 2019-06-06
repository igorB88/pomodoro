# django
from django.contrib import admin

# my
from app.actions import mark_contact_duplicate_action, mark_contact_rejected_action, upload_audio_action
from app.models import TelegramUser, Pomodoro, Project, Rest, Contact, MessageSender, Audio


class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'name', 'current_project', 'status',
                    'pomodoro_duration', 'pomodoro_rest', 'pomodoro_big_rest', 'pomodoro_session_count')
    search_fields = ('first_name', 'last_name')
    readonly_fields = ('state', )
    date_hierarchy = 'create_date'
    list_filter = ('status', )


class PomodoroAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'project', 'start_date', 'end_date',
                    'duration', 'real_duration', 'telegram_user')
    list_filter = ('status', )
    readonly_fields = ('task_id', )
    date_hierarchy = 'create_date'


class RestAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'project', 'start_date', 'end_date',
                    'duration', 'real_duration', 'telegram_user')
    list_filter = ('status', )
    readonly_fields = ('task_id', )
    date_hierarchy = 'create_date'


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'telegram_user', 'total_pomodoros', 'total_rest')
    search_fields = ('name', )


class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'telegram_user', 'answer', 'status')
    search_fields = ('message', )
    list_filter = ('status', )

    actions = (mark_contact_duplicate_action, mark_contact_rejected_action)


class MessageSenderAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'status', 'title')
    list_filter = ('category', 'status')
    readonly_fields = ('status', )


class AudioAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'audio_id')
    search_fields = ('name', 'audio_id')
    readonly_fields = ('audio_id', )
    list_filter = ('category', )

    actions = (upload_audio_action, )


admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(Pomodoro, PomodoroAdmin)
admin.site.register(Rest, RestAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(MessageSender, MessageSenderAdmin)
admin.site.register(Audio, AudioAdmin)
