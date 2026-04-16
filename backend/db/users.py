import hashlib
import os

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
