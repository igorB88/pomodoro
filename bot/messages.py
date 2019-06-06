# django
from django.conf import settings


start_message = """
☘ Bot that allows you to track your time using ⏲pomodoro technique.
You can read more about this https://en.wikipedia.org/wiki/Pomodoro_Technique

If you like this bot you can add review: https://telegram.me/storebot?start={}
""".format(settings.TELEGRAM_BOT_NAME)

empty_command_message = """
Here available commands
"""

stats_select_message = """
Select stats to show
"""

contact_us_message = """
Contact us, you can send your propositions, claims, testimonials or whatever your want. Drop us few lines, thank you!
"""

contact_us_sent = """
Thank you for your message!
"""

admin_message = """
You are in admin interface
"""

pomodoro_started_message = """
Pomodoro started
"""

pomodoro_ended_message = """
Pomodoro ended
"""

first_pomodoro_message = """
You've just completed your pomodoro. If you like our bot you can send us feedback /contact.
"""

pomodoro_rest_started_message = """
Rest started
"""

pomodoro_rest_stopped_message = """
Rest stopped
"""

pomodoro_rest_ended_message = """
Rest ended
"""

pomodoro_in_progress_message = """
Pomodoro is in progress.
"""

pomodoro_no_message = """
NO pomodoro is in progress.
"""

pomodoro_stopped_message = """
Pomodoro was stopped before end
"""

stats_message = """
Stats for {period} for project {project.name}:
  Finished: {count_finished}
  Unfinished: {count_unfinished}
  In progress: {count_in_progress}
  Total: {count}
  Total time: {total_duration}
"""

no_stats_message = """
No stats for this period
"""

bad_period_message = """
Period is invalid use, day, week or month
"""

project_set_message = """
Current project is {project.name}
"""

project_info_message = "Set project: {project.name}, total: {project.total_pomodoros}"


admin_count_message = """Count {model} is: {count}"""

admin_count_active = """
Active pomodoros - {active_pomodoros}, active rest - {active_rests}
"""

bad_command_message = """
Unknown command. Please retry
"""

list_projects_message = """
List of all projects
"""

new_project_message = """
Enter new project name
"""

not_implemented_message = """
Not implemented yet
"""

settings_message = """
Settings
"""

settings_pomodoro_message = """
Please provide length of pomodoro in minutes. Current is {u.pomodoro_minutes} minutes.
"""

settings_pomodoro_set_message = """
Pomodoro length is set to {u.pomodoro_minutes} minutes
"""

settings_rest_message = """
Please provide length of small rest between pomodoros in minutes. Current is {u.rest_minutes} minutes.
"""

settings_rest_set_message = """
Small rest length is set to {u.rest_minutes} minutes
"""

settings_big_rest_message = """
Please provide length of big rest between pomodoros in minutes. Current is {u.big_rest_minutes} minutes.
"""

settings_big_rest_set_message = """
Big rest length is set to {u.big_rest_minutes} minutes
"""

settings_session_count_message = """
Please provide number of pomodoros in one session. Usually one session has 4 pomodoros, and rest between sessions is bigger (usually 15 minutes).
Current is {u.pomodoro_session_count} pomodoros.
"""

settings_session_count_set_message = """
Pomodoros in one session is set to {u.big_rest_minutes} pomodoros
"""

settings_error_minutes = """
Can not parse number of minutes. It can be from 1 to 60. Please provide correct number
"""

settings_error_session = """
Can not parse session count. It can be from 1 to 60. Please provide correct number
"""
