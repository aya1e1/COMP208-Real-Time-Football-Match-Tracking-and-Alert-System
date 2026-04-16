import hashlib
import os
import sqlite3

from backend.db import database

try:
    from flask_login import LoginManager, UserMixin
except ModuleNotFoundError:
    class UserMixin:
        @property
        def is_authenticated(self):
            return True

        @property
        def is_active(self):
            return True

        @property
        def is_anonymous(self):
            return False

        def get_id(self):
            return str(self.id)

    class LoginManager:
        def __init__(self):
            self.login_view = None
            self._user_loader = None

        def init_app(self, app):
            self.app = app

        def user_loader(self, callback):
            self._user_loader = callback
            return callback


login_manager = LoginManager()


class User(UserMixin):
    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        password_hash: str,
        created_date: str | None = None,
    ) -> None:
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_date = created_date

    @classmethod
    def from_row(cls, row: dict | None) -> "User | None":
        if not row:
            return None

        return cls(
            user_id=row["UserID"],
            username=row["Username"],
            email=row["Email"],
            password_hash=row["PasswordHash"],
            created_date=row.get("CreatedDate"),
        )

    def to_dict(self) -> dict:
        return {
            "UserID": self.id,
            "Username": self.username,
            "Email": self.email,
            "CreatedDate": self.created_date,
        }


def init_login_manager(app) -> None:
    login_manager.login_view = "auth.login_page"
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return get_user_by_id(int(user_id))
    except (TypeError, ValueError):
        return None


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def _fetch_one(sql: str, params: tuple) -> dict | None:
    rows = database.query(sql, params)
    return rows[0] if rows else None


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    password_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False

    salt, password_hash = stored_hash.split("$", 1)
    calculated_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return calculated_hash == password_hash


def create_user(username: str, email: str, password: str) -> User:
    user_id = database.execute(
        """
        INSERT INTO Users (Username, Email, PasswordHash)
        VALUES (?, ?, ?)
        """,
        (username.strip(), _normalise_email(email), hash_password(password)),
    )
    return get_user_by_id(user_id)


def get_user_by_id(user_id: int) -> User | None:
    row = _fetch_one(
        """
        SELECT UserID, Username, Email, PasswordHash, CreatedDate
        FROM Users
        WHERE UserID = ?
        """,
        (user_id,),
    )
    return User.from_row(row)


def get_user_by_username(username: str) -> User | None:
    row = _fetch_one(
        """
        SELECT UserID, Username, Email, PasswordHash, CreatedDate
        FROM Users
        WHERE Username = ?
        """,
        (username.strip(),),
    )
    return User.from_row(row)


def get_user_by_email(email: str) -> User | None:
    row = _fetch_one(
        """
        SELECT UserID, Username, Email, PasswordHash, CreatedDate
        FROM Users
        WHERE Email = ?
        """,
        (_normalise_email(email),),
    )
    return User.from_row(row)


def authenticate_user(identifier: str, password: str) -> User | None:
    identifier = identifier.strip()
    user = get_user_by_email(identifier) if "@" in identifier else get_user_by_username(identifier)

    if not user or not verify_password(password, user.password_hash):
        return None

    return user


def list_favourite_teams(user_id: int) -> list[dict]:
    return database.query(
        """
        SELECT
            ft.FavouriteTeamID,
            ft.UserID,
            ft.TeamID,
            ft.CreatedDate,
            t.Name,
            t.Abbreviation,
            t.LogoURL,
            t.City,
            t.Stadium
        FROM FavouriteTeams ft
        JOIN Teams t
            ON ft.TeamID = t.TeamID
        WHERE ft.UserID = ?
        ORDER BY t.Name
        """,
        (user_id,),
    )


def add_favourite_team(user_id: int, team_id: int) -> int:
    return database.execute(
        """
        INSERT INTO FavouriteTeams (UserID, TeamID)
        VALUES (?, ?)
        """,
        (user_id, team_id),
    )


def remove_favourite_team(user_id: int, team_id: int) -> None:
    database.execute(
        """
        DELETE FROM FavouriteTeams
        WHERE UserID = ? AND TeamID = ?
        """,
        (user_id, team_id),
    )


def list_favourite_players(user_id: int) -> list[dict]:
    return database.query(
        """
        SELECT
            fp.FavouritePlayerID,
            fp.UserID,
            fp.PlayerID,
            fp.CreatedDate,
            p.FirstName,
            p.LastName,
            p.Name,
            p.MainPosition,
            p.Nationality
        FROM FavouritePlayers fp
        JOIN Player p
            ON fp.PlayerID = p.PlayerID
        WHERE fp.UserID = ?
        ORDER BY p.Name
        """,
        (user_id,),
    )


def add_favourite_player(user_id: int, player_id: int) -> int:
    return database.execute(
        """
        INSERT INTO FavouritePlayers (UserID, PlayerID)
        VALUES (?, ?)
        """,
        (user_id, player_id),
    )


def remove_favourite_player(user_id: int, player_id: int) -> None:
    database.execute(
        """
        DELETE FROM FavouritePlayers
        WHERE UserID = ? AND PlayerID = ?
        """,
        (user_id, player_id),
    )


def get_notification_preferences(user_id: int) -> list[dict]:
    return database.query(
        """
        SELECT
            unp.PreferenceID,
            unp.UserID,
            unp.TeamID,
            unp.NotifyGoals,
            unp.NotifyCards,
            unp.NotifySubstitutions,
            t.Name AS TeamName
        FROM UserNotificationPreferences unp
        LEFT JOIN Teams t
            ON unp.TeamID = t.TeamID
        WHERE unp.UserID = ?
        ORDER BY t.Name, unp.PreferenceID
        """,
        (user_id,),
    )


def get_notification_preference(user_id: int, team_id: int | None) -> dict | None:
    if team_id is None:
        sql = """
            SELECT PreferenceID, UserID, TeamID, NotifyGoals, NotifyCards, NotifySubstitutions
            FROM UserNotificationPreferences
            WHERE UserID = ? AND TeamID IS NULL
            LIMIT 1
        """
        params = (user_id,)
    else:
        sql = """
            SELECT PreferenceID, UserID, TeamID, NotifyGoals, NotifyCards, NotifySubstitutions
            FROM UserNotificationPreferences
            WHERE UserID = ? AND TeamID = ?
            LIMIT 1
        """
        params = (user_id, team_id)

    return _fetch_one(sql, params)


def upsert_notification_preference(
    user_id: int,
    team_id: int | None,
    *,
    notify_goals: bool = True,
    notify_cards: bool = True,
    notify_substitutions: bool = False,
) -> None:
    existing_preference = get_notification_preference(user_id, team_id)

    if existing_preference:
        database.execute(
            """
            UPDATE UserNotificationPreferences
            SET NotifyGoals = ?, NotifyCards = ?, NotifySubstitutions = ?
            WHERE PreferenceID = ?
            """,
            (
                int(notify_goals),
                int(notify_cards),
                int(notify_substitutions),
                existing_preference["PreferenceID"],
            ),
        )
        return

    database.execute(
        """
        INSERT INTO UserNotificationPreferences
        (
            UserID,
            TeamID,
            NotifyGoals,
            NotifyCards,
            NotifySubstitutions
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            team_id,
            int(notify_goals),
            int(notify_cards),
            int(notify_substitutions),
        ),
    )


def delete_notification_preference(user_id: int, team_id: int | None) -> None:
    if team_id is None:
        database.execute(
            """
            DELETE FROM UserNotificationPreferences
            WHERE UserID = ? AND TeamID IS NULL
            """,
            (user_id,),
        )
        return

    database.execute(
        """
        DELETE FROM UserNotificationPreferences
        WHERE UserID = ? AND TeamID = ?
        """,
        (user_id, team_id),
    )


def get_event_vote(user_id: int, fixture_id: int, event_id: int) -> dict | None:
    return _fetch_one(
        """
        SELECT VoteID, UserID, FixtureID, EventID, VoteType, CreatedDate, UpdatedDate
        FROM EventVotes
        WHERE UserID = ? AND FixtureID = ? AND EventID = ?
        LIMIT 1
        """,
        (user_id, fixture_id, event_id),
    )


def update_event_vote(user_id: int, fixture_id: int, event_id: int, vote_type: str) -> dict | None:
    if vote_type not in {"like", "dislike"}:
        raise ValueError("vote_type must be 'like' or 'dislike'")

    existing_vote = get_event_vote(user_id, fixture_id, event_id)

    if existing_vote:
        database.execute(
            """
            UPDATE EventVotes
            SET VoteType = ?, UpdatedDate = CURRENT_TIMESTAMP
            WHERE VoteID = ?
            """,
            (vote_type, existing_vote["VoteID"]),
        )
        return get_event_vote(user_id, fixture_id, event_id)

    try:
        database.execute(
            """
            INSERT INTO EventVotes (UserID, FixtureID, EventID, VoteType)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, fixture_id, event_id, vote_type),
        )
    except sqlite3.IntegrityError as exc:
        raise ValueError("fixture_id and event_id must reference a valid event") from exc

    return get_event_vote(user_id, fixture_id, event_id)


def remove_event_vote(user_id: int, fixture_id: int, event_id: int) -> None:
    database.execute(
        """
        DELETE FROM EventVotes
        WHERE UserID = ? AND FixtureID = ? AND EventID = ?
        """,
        (user_id, fixture_id, event_id),
    )


def list_event_votes(user_id: int) -> list[dict]:
    return database.query(
        """
        SELECT
            ev.VoteID,
            ev.UserID,
            ev.FixtureID,
            ev.EventID,
            ev.VoteType,
            ev.CreatedDate,
            ev.UpdatedDate,
            e.PlayerID,
            e.PlayerName,
            e.AssistPlayerID,
            e.AssistPlayerName,
            e.TeamID,
            t.Name AS TeamName,
            e.EventType,
            e.Detail,
            e.Comments,
            e.EventMinute,
            e.ExtraMinute,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            f.MatchDate,
            f.Status,
            COALESCE(vs.LikeCount, 0) AS Likes,
            COALESCE(vs.DislikeCount, 0) AS Dislikes
        FROM EventVotes ev
        JOIN Events e
            ON ev.FixtureID = e.FixtureID
           AND ev.EventID = e.EventID
        LEFT JOIN Teams t
            ON e.TeamID = t.TeamID
        JOIN Fixtures f
            ON ev.FixtureID = f.FixtureID
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
        LEFT JOIN (
            SELECT
                FixtureID,
                EventID,
                SUM(CASE WHEN VoteType = 'like' THEN 1 ELSE 0 END) AS LikeCount,
                SUM(CASE WHEN VoteType = 'dislike' THEN 1 ELSE 0 END) AS DislikeCount
            FROM EventVotes
            GROUP BY FixtureID, EventID
        ) vs
            ON ev.FixtureID = vs.FixtureID
           AND ev.EventID = vs.EventID
        WHERE ev.UserID = ?
        ORDER BY f.MatchDate DESC, e.EventMinute ASC, e.ExtraMinute ASC, e.EventID ASC
        """,
        (user_id,),
    )


def get_event_vote_summaries(
    fixture_id: int,
    *,
    user_id: int | None = None,
) -> dict[tuple[int, int], dict]:
    vote_rows = database.query(
        """
        SELECT
            ev.FixtureID,
            ev.EventID,
            SUM(CASE WHEN ev.VoteType = 'like' THEN 1 ELSE 0 END) AS LikeCount,
            SUM(CASE WHEN ev.VoteType = 'dislike' THEN 1 ELSE 0 END) AS DislikeCount
        FROM EventVotes ev
        WHERE ev.FixtureID = ?
        GROUP BY ev.FixtureID, ev.EventID
        """,
        (fixture_id,),
    )

    summary_by_event = {
        (row["FixtureID"], row["EventID"]): {
            "likes": row["LikeCount"] or 0,
            "dislikes": row["DislikeCount"] or 0,
            "user_vote": None,
        }
        for row in vote_rows
    }

    if user_id is None:
        return summary_by_event

    user_votes = database.query(
        """
        SELECT FixtureID, EventID, VoteType
        FROM EventVotes
        WHERE UserID = ? AND FixtureID = ?
        """,
        (user_id, fixture_id),
    )

    for row in user_votes:
        event_key = (row["FixtureID"], row["EventID"])
        summary = summary_by_event.setdefault(
            event_key,
            {"likes": 0, "dislikes": 0, "user_vote": None},
        )
        summary["user_vote"] = row["VoteType"]

    return summary_by_event
