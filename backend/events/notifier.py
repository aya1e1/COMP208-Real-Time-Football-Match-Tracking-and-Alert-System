"""notifier.py - User notification engine."""
from backend.db.database import query

_notifications = []
class Notifier:
    def notify(self, fixture_id, team_id, event_type, detail, minute):
        userList = []
        if event_type=="Goal":
            userList = query("SELECT DISTINCT t.UserID FROM UserFavouriteTeams t JOIN UserNotificationPreferences p ON t.UserID = p.UserID AND t.TeamID = p.TeamID WHERE t.TeamID = ? AND p.NotifyGoals = TRUE", team_id)
            for row in userList:
                _notifications.append({
                    "UserID": row["UserID"],
                    "TeamID": team_id,
                    "message": "GOAL",
                    "detail": detail,
                    "minute": minute
                })

        elif event_type=="Card":
            userList = query("SELECT DISTINCT t.UserID FROM UserFavouriteTeams t JOIN UserNotificationPreferences p ON t.UserID = p.UserID AND t.TeamID = p.TeamID WHERE t.TeamID = ? AND p.NotifyCards = TRUE", team_id)
            for row in userList:
                _notifications.append({
                    "UserID": row["UserID"],
                    "TeamID": team_id,
                    "message": "CARD",
                    "detail": detail,
                    "minute": minute
                })

        elif event_type=="Substitution":
            userList = query("SELECT DISTINCT t.UserID FROM UserFavouriteTeams t JOIN UserNotificationPreferences p ON t.UserID = p.UserID AND t.TeamID = p.TeamID WHERE t.TeamID = ? AND p.NotifySubstitutions = TRUE", team_id)
            for row in userList:
                _notifications.append({
                    "UserID": row["UserID"],
                    "TeamID": team_id,
                    "message": "SUBSTITUTION",
                    "detail": detail,
                    "minute": minute
                })


def get_pending_notifications():
    global _notifications
    notifs = _notifications
    _notifications = []
    return notifs