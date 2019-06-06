# django
from django.db import models

# other
from jsonfield import JSONField


class StateMixin(models.Model):
    STATE_KEY = 'state'

    state = JSONField(null=True, blank=True)

    class Meta(object):
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.state:
            self.state = {}

    def set_state(self, key, value):
        self.state[key] = value
        self.save()

    def get_state(self, key, default=None):
        return self.state.get(key, default)

    def remove_state(self, key):
        if key in self.state:
            del self.state[key]
            self.save()

    def push_state_machine(self, new_state):
        state = self.get_state(StateMixin.STATE_KEY, [])
        state.append(new_state)
        self.set_state(StateMixin.STATE_KEY, state)

    def pop_state_machine(self):
        state = self.get_state(StateMixin.STATE_KEY, [])
        res = state.pop()
        self.set_state(StateMixin.STATE_KEY, state)
        return res

    def clear_state_machine(self):
        self.set_state(StateMixin.STATE_KEY, [])

    def get_state_machine(self):
        state = self.get_state(StateMixin.STATE_KEY, [])
        return state[-1] if state else None
