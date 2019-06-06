# common
import calendar
import datetime

# django
from django.contrib.auth import get_user_model


def chunker(seq, size):
    if len(seq) == 0:
      return []
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def increment_month(when):
    days = calendar.monthrange(when.year, when.month)[1]
    return when + datetime.timedelta(days=days)


def get_admin_emails():
    admins = get_user_model().objects.filter(is_superuser=True)
    recipients = [u.email for u in admins if u.email]
    return recipients
