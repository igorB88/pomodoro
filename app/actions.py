#
from app.tasks import upload_telegram_audio_task


def mark_contact_rejected_action(modeladmin, request, queryset):
    for contact in queryset:
        contact.status = 'rejected'
        contact.save()


def mark_contact_duplicate_action(modeladmin, request, queryset):
    for contact in queryset:
        contact.status = 'duplicate'
        contact.save()


def upload_audio_action(modeladmin, request, queryset):
    for audio in queryset:
        upload_telegram_audio_task.apply_async(args=(audio.id, ))
