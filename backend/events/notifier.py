"""notifier.py - User notification engine."""
from backend.db.batabase import query

_notifications = []


class Notifier:

    def notify(self, fixture_id, team_id, event_type, detail, minute):
