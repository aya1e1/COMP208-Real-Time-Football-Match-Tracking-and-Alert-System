"""notifier.py - User notification engine."""
from backend.db.database import query

_notifications = []


class Notifier:

    def notify(self, fixture_id, team_id, event_type, detail, minute):
        notification = {
            "fixture_id" : fixture_id,
            "team_id" : team_id,
            "event_type" : event_type,
            "detail" : detail,
            "minute" : minute
        }
        
        _notifications.append(notification)
        
        print(f"[{minute}'] {event_type} - {detail} (Team {team_id})")
