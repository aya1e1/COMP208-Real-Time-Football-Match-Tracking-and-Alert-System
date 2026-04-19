from datetime import datetime

from flask import Blueprint, jsonify, request

try:
    from flask_login import current_user, login_required
except ModuleNotFoundError:
    def login_required(func):
        return func

    class _AnonymousUser:
        is_authenticated = False
        id = None

    current_user = _AnonymousUser()

from backend.db import database
from backend.db import users as user_repo
from backend.data_sync import (
    sync_events,
    sync_fixture_statistics,
    sync_fixtures,
    sync_standings,
    sync_teams,
    sync_team_statistics,
)

api_bp = Blueprint("api", __name__)

COUNTRY_CODE_MAP = {
    "Argentina": "ARG",
    "Belgium": "BEL",
    "Brazil": "BRA",
    "England": "ENG",
    "France": "FRA",
    "Germany": "GER",
    "Italy": "ITA",
    "Netherlands": "NED",
    "Portugal": "POR",
    "Saudi-Arabia": "KSA",
    "Scotland": "SCO",
    "Spain": "ESP",
    "Turkey": "TUR",
    "USA": "USA",
}
COUNTRY_NAME_BY_CODE = {code: name for name, code in COUNTRY_CODE_MAP.items()}
LIVE_STATUSES = ("1H", "2H", "HT", "ET", "P")
FINISHED_STATUSES = ("FT", "AET", "PEN")


def _is_truthy_query_param(value: str | None) -> bool:
    if value is None:
        return False

    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_country_filter(country_value: str | None) -> str | None:
    if country_value is None:
        return None

    normalized = str(country_value).strip()
    if not normalized:
        return None

    normalized_upper = normalized.upper()
    if normalized_upper == "ALL":
        return None

    if len(normalized_upper) <= 3:
        return COUNTRY_NAME_BY_CODE.get(normalized_upper, normalized)

    return normalized


def _last_five_form_chars(form: str | None) -> str:
    if not form:
        return ""
    return form[-5:]


def _build_location_stats(team_stats: dict, venue: str) -> dict:
    is_home = venue == "home"

    wins = team_stats["WinsHome"] if is_home else team_stats["WinsAway"]
    draws = team_stats["DrawsHome"] if is_home else team_stats["DrawsAway"]
    losses = team_stats["LossesHome"] if is_home else team_stats["LossesAway"]
    goals_for_average = (
        team_stats["GoalsForAverageHome"]
        if is_home
        else team_stats["GoalsForAverageAway"]
    )
    goals_against_average = (
        team_stats["GoalsAgainstAverageHome"]
        if is_home
        else team_stats["GoalsAgainstAverageAway"]
    )
    failed_to_score = (
        team_stats["FailedToScoreHome"]
        if is_home
        else team_stats["FailedToScoreAway"]
    )

    return {
        "last_five_form": _last_five_form_chars(team_stats.get("Form")),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for_average": goals_for_average,
        "goals_against_average": goals_against_average,
        "failed_to_score": failed_to_score,
    }


def _build_team_overview(team_stats: dict) -> dict:
    return {
        "home": _build_location_stats(team_stats, "home"),
        "away": _build_location_stats(team_stats, "away"),
    }


def _get_h2h_fixtures(
    home_team_id: int,
    away_team_id: int,
    excluded_fixture_id: int,
) -> list[dict]:
    sql = """
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            ht.LogoURL AS HomeTeamLogoURL,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
            at.LogoURL AS AwayTeamLogoURL,
            f.Location,
            f.MatchDate,
            f.HomeScore,
            f.AwayScore,
            f.Status,
            f.Elapsed
        FROM Fixtures f
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
        WHERE f.HomeTeamID = ?
          AND f.AwayTeamID = ?
          AND f.FixtureID != ?
        ORDER BY f.MatchDate DESC
        LIMIT 5
    """
    return database.query(sql, (home_team_id, away_team_id, excluded_fixture_id))


def _get_fixtures_for_team_ids(
    team_ids: list[int],
    *,
    limit: int = 5,
    match_date_before: str | None = None,
    match_date_after: str | None = None,
    order: str = "DESC",
) -> list[dict]:
    if not team_ids:
        return []

    normalized_order = "ASC" if order.upper() == "ASC" else "DESC"
    placeholders = ", ".join("?" for _ in team_ids)
    sql = f"""
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            ht.LogoURL AS HomeTeamLogoURL,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
            at.LogoURL AS AwayTeamLogoURL,
            f.Location,
            f.MatchDate,
            f.HomeScore,
            f.AwayScore,
            f.Status,
            f.Elapsed
        FROM Fixtures f
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
        WHERE (
            f.HomeTeamID IN ({placeholders})
            OR f.AwayTeamID IN ({placeholders})
        )
    """
    params = [*team_ids, *team_ids]

    if match_date_before:
        sql += " AND f.MatchDate <= ?"
        params.append(match_date_before)

    if match_date_after:
        sql += " AND f.MatchDate > ?"
        params.append(match_date_after)

    sql += f" ORDER BY f.MatchDate {normalized_order} LIMIT ?"
    params.append(limit)
    return database.query(sql, tuple(params))


def _get_paginated_fixtures_for_team_ids(
    team_ids: list[int],
    *,
    page: int = 1,
    per_page: int = 5,
    match_date_before: str | None = None,
    match_date_after: str | None = None,
    order: str = "DESC",
) -> tuple[list[dict], dict]:
    if not team_ids:
        return [], {
            "page": 1,
            "per_page": per_page,
            "total_fixtures": 0,
            "total_pages": 1,
            "has_previous": False,
            "has_next": False,
        }

    normalized_order = "ASC" if order.upper() == "ASC" else "DESC"
    placeholders = ", ".join("?" for _ in team_ids)
    from_sql = f"""
        FROM Fixtures f
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
        WHERE (
            f.HomeTeamID IN ({placeholders})
            OR f.AwayTeamID IN ({placeholders})
        )
    """
    params = [*team_ids, *team_ids]

    if match_date_before:
        from_sql += " AND f.MatchDate <= ?"
        params.append(match_date_before)

    if match_date_after:
        from_sql += " AND f.MatchDate > ?"
        params.append(match_date_after)

    select_sql = f"""
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            ht.LogoURL AS HomeTeamLogoURL,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
            at.LogoURL AS AwayTeamLogoURL,
            f.Location,
            f.MatchDate,
            f.HomeScore,
            f.AwayScore,
            f.Status,
            f.Elapsed
        {from_sql}
        ORDER BY f.MatchDate {normalized_order}
        LIMIT ? OFFSET ?
    """
    count_sql = f"""
        SELECT COUNT(*) AS TotalFixtures
        {from_sql}
    """

    total_count_row = database.query(count_sql, tuple(params))
    total_fixtures = total_count_row[0]["TotalFixtures"] if total_count_row else 0
    total_pages = max(1, (total_fixtures + per_page - 1) // per_page)
    safe_page = min(max(1, page), total_pages)
    offset = (safe_page - 1) * per_page
    fixtures = database.query(select_sql, tuple([*params, per_page, offset]))

    return fixtures, {
        "page": safe_page,
        "per_page": per_page,
        "total_fixtures": total_fixtures,
        "total_pages": total_pages,
        "has_previous": safe_page > 1,
        "has_next": safe_page < total_pages,
    }


def _get_recent_fixtures_for_league_season(
    league_id: int,
    year: int,
    *,
    limit: int = 5,
    match_date_before: str | None = None,
) -> list[dict]:
    sql = """
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            ht.LogoURL AS HomeTeamLogoURL,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
            at.LogoURL AS AwayTeamLogoURL,
            f.Location,
            f.MatchDate,
            f.HomeScore,
            f.AwayScore,
            f.Status,
            f.Elapsed
        FROM Fixtures f
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
        WHERE f.LeagueID = ?
          AND f.Year = ?
    """
    params = [league_id, year]

    if match_date_before:
        sql += " AND f.MatchDate <= ?"
        params.append(match_date_before)

    sql += " ORDER BY f.MatchDate DESC LIMIT ?"
    params.append(limit)

    return database.query(sql, tuple(params))


def _get_paginated_recent_fixtures_for_league_season(
    league_id: int,
    year: int,
    *,
    page: int = 1,
    per_page: int = 5,
    match_date_before: str | None = None,
) -> tuple[list[dict], dict]:
    from_sql = """
        FROM Fixtures f
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
        WHERE f.LeagueID = ?
          AND f.Year = ?
    """
    params = [league_id, year]

    if match_date_before:
        from_sql += " AND f.MatchDate <= ?"
        params.append(match_date_before)

    select_sql = f"""
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            ht.LogoURL AS HomeTeamLogoURL,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
            at.LogoURL AS AwayTeamLogoURL,
            f.Location,
            f.MatchDate,
            f.HomeScore,
            f.AwayScore,
            f.Status,
            f.Elapsed
        {from_sql}
        ORDER BY f.MatchDate DESC
        LIMIT ? OFFSET ?
    """
    count_sql = f"""
        SELECT COUNT(*) AS TotalFixtures
        {from_sql}
    """

    total_count_row = database.query(count_sql, tuple(params))
    total_fixtures = total_count_row[0]["TotalFixtures"] if total_count_row else 0
    total_pages = max(1, (total_fixtures + per_page - 1) // per_page)
    safe_page = min(max(1, page), total_pages)
    offset = (safe_page - 1) * per_page
    fixtures = database.query(select_sql, tuple([*params, per_page, offset]))

    return fixtures, {
        "page": safe_page,
        "per_page": per_page,
        "total_fixtures": total_fixtures,
        "total_pages": total_pages,
        "has_previous": safe_page > 1,
        "has_next": safe_page < total_pages,
    }


def _get_team(team_id: int) -> dict | None:
    rows = database.query(
        """
        SELECT
            t.TeamID,
            t.Name,
            t.Abbreviation,
            t.LogoURL,
            t.City,
            t.Stadium
        FROM Teams t
        WHERE t.TeamID = ?
        LIMIT 1
        """,
        (team_id,),
    )
    return rows[0] if rows else None


def _is_favourite_team(team_id: int) -> bool:
    if not getattr(current_user, "is_authenticated", False):
        return False

    rows = database.query(
        """
        SELECT 1
        FROM UserFavouriteTeams
        WHERE UserID = ? AND TeamID = ?
        LIMIT 1
        """,
        (current_user.id, team_id),
    )
    return bool(rows)


def _get_team_statistics_row(team_id: int) -> dict | None:
    rows = database.query(
        """
        SELECT
            ts.LeagueID,
            l.Name AS LeagueName,
            ts.Year,
            ts.TeamID,
            ts.Form,
            ts.WinsHome,
            ts.WinsAway,
            ts.DrawsHome,
            ts.DrawsAway,
            ts.LossesHome,
            ts.LossesAway,
            ts.GoalsForAverageHome,
            ts.GoalsForAverageAway,
            ts.GoalsAgainstAverageHome,
            ts.GoalsAgainstAverageAway,
            ts.FailedToScoreHome,
            ts.FailedToScoreAway
        FROM TeamStatistics ts
        JOIN League l
            ON ts.LeagueID = l.LeagueID
        WHERE ts.TeamID = ?
        ORDER BY ts.Year DESC, ts.LeagueID ASC
        LIMIT 1
        """,
        (team_id,),
    )
    return rows[0] if rows else None


def _get_team_statistics_context(team_id: int) -> dict | None:
    rows = database.query(
        """
        SELECT
            LeagueID,
            Year
        FROM Fixtures
        WHERE HomeTeamID = ?
           OR AwayTeamID = ?
        ORDER BY MatchDate DESC
        LIMIT 1
        """,
        (team_id, team_id),
    )
    return rows[0] if rows else None


def _require_integer_field(name: str) -> int | None:
    payload = request.get_json(silent=True) or {}
    value = payload.get(name)

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_event_vote_payload(fixture_id: int, event_id: int) -> dict:
    user_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
    vote_summary = user_repo.get_event_vote_summaries(fixture_id, user_id=user_id).get(
        (fixture_id, event_id),
        {"likes": 0, "dislikes": 0, "user_vote": None},
    )
    return {
        "FixtureID": fixture_id,
        "EventID": event_id,
        "Likes": vote_summary["likes"],
        "Dislikes": vote_summary["dislikes"],
        "UserVote": vote_summary["user_vote"],
    }


@api_bp.route("/me")
@login_required
def me():
    return jsonify({"user": current_user.to_dict()})


@api_bp.route("/me/favourite-teams")
@login_required
def favourite_teams():
    teams = user_repo.list_favourite_teams(current_user.id)
    return jsonify({"data": teams})


@api_bp.route("/me/dashboard")
@login_required
def dashboard():
    teams = user_repo.list_favourite_teams(current_user.id)
    team_ids = [int(team["TeamID"]) for team in teams if team.get("TeamID") is not None]
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    recent_fixtures = _get_fixtures_for_team_ids(
        team_ids,
        limit=5,
        match_date_before=current_timestamp,
        order="DESC",
    )
    upcoming_fixtures = _get_fixtures_for_team_ids(
        team_ids,
        limit=5,
        match_date_after=current_timestamp,
        order="ASC",
    )

    return jsonify({
        "data": {
            "favourite_teams": teams,
            "recent_fixtures": recent_fixtures,
            "upcoming_fixtures": upcoming_fixtures,
        }
    })


@api_bp.route("/me/favourite-teams", methods=["POST"])
@login_required
def add_favourite_team():
    team_id = _require_integer_field("team_id")
    if team_id is None:
        return jsonify({"error": "team_id is required and must be an integer"}), 400

    try:
        user_repo.add_favourite_team(current_user.id, team_id)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"success": True}), 201


@api_bp.route("/me/favourite-teams/<int:team_id>", methods=["DELETE"])
@login_required
def delete_favourite_team(team_id):
    user_repo.remove_favourite_team(current_user.id, team_id)
    return jsonify({"success": True})


@api_bp.route("/me/favourite-players")
@login_required
def favourite_players():
    players = user_repo.list_favourite_players(current_user.id)
    return jsonify({"data": players})


@api_bp.route("/me/favourite-players", methods=["POST"])
@login_required
def add_favourite_player():
    player_id = _require_integer_field("player_id")
    if player_id is None:
        return jsonify({"error": "player_id is required and must be an integer"}), 400

    try:
        user_repo.add_favourite_player(current_user.id, player_id)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"success": True}), 201


@api_bp.route("/me/favourite-players/<int:player_id>", methods=["DELETE"])
@login_required
def delete_favourite_player(player_id):
    user_repo.remove_favourite_player(current_user.id, player_id)
    return jsonify({"success": True})


@api_bp.route("/me/notification-preferences")
@login_required
def notification_preferences():
    preferences = user_repo.get_notification_preferences(current_user.id)
    return jsonify({"data": preferences})


@api_bp.route("/me/notification-preferences", methods=["PUT"])
@login_required
def update_notification_preferences():
    payload = request.get_json(silent=True) or {}
    team_id_value = payload.get("team_id")
    team_id = None if team_id_value in (None, "") else _require_integer_field("team_id")

    if team_id_value not in (None, "") and team_id is None:
        return jsonify({"error": "team_id must be an integer when provided"}), 400

    user_repo.upsert_notification_preference(
        current_user.id,
        team_id,
        notify_goals=bool(payload.get("notify_goals", True)),
        notify_cards=bool(payload.get("notify_cards", True)),
        notify_substitutions=bool(payload.get("notify_substitutions", False)),
    )
    preference = user_repo.get_notification_preference(current_user.id, team_id)
    return jsonify({"data": preference})


@api_bp.route("/me/event-votes")
@login_required
def event_votes():
    votes = user_repo.list_event_votes(current_user.id)
    return jsonify({"data": votes})


@api_bp.route("/me/event-votes", methods=["PUT"])
@login_required
def update_event_vote():
    fixture_id = _require_integer_field("fixture_id")
    event_id = _require_integer_field("event_id")
    payload = request.get_json(silent=True) or {}
    vote_type = payload.get("vote_type")

    if fixture_id is None:
        return jsonify({"error": "fixture_id is required and must be an integer"}), 400

    if event_id is None:
        return jsonify({"error": "event_id is required and must be an integer"}), 400

    if vote_type not in {"like", "dislike"}:
        return jsonify({"error": "vote_type is required and must be 'like' or 'dislike'"}), 400

    try:
        user_repo.update_event_vote(current_user.id, fixture_id, event_id, vote_type)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"data": _get_event_vote_payload(fixture_id, event_id)})


@api_bp.route("/me/event-votes", methods=["DELETE"])
@login_required
def delete_event_vote():
    fixture_id = _require_integer_field("fixture_id")
    event_id = _require_integer_field("event_id")

    if fixture_id is None:
        return jsonify({"error": "fixture_id is required and must be an integer"}), 400

    if event_id is None:
        return jsonify({"error": "event_id is required and must be an integer"}), 400

    user_repo.remove_event_vote(current_user.id, fixture_id, event_id)
    return jsonify({"data": _get_event_vote_payload(fixture_id, event_id)})


@api_bp.route("/leagues")
def leagues():
    sql = """
        SELECT LeagueID, Name, Country, LogoURL
        FROM League
        ORDER BY Name
    """
    leagues = database.query(sql)
    return jsonify(leagues)


@api_bp.route("/leagues/<int:league_id>/seasons/<int:year>/teams")
def league_teams(league_id, year):

    league_sql = """
        SELECT
            l.LeagueID,
            l.Name,
            l.Country,
            l.LogoURL,
            s.Year,
            s.Current
        FROM League l
        JOIN Seasons s
            ON l.LeagueID = s.LeagueID
        WHERE l.LeagueID = ?
          AND s.Year = ?
    """
    league = database.query(league_sql, (league_id, year))

    if not league:
        return jsonify({"error": "League season not found"}), 404

    teams_sql = """
        SELECT DISTINCT
            t.TeamID,
            t.Name,
            t.Abbreviation,
            t.City,
            t.Stadium
        FROM SeasonTeams st
        JOIN Teams t
            ON st.TeamID = t.TeamID
        WHERE st.LeagueID = ?
          AND st.Year = ?
        ORDER BY t.Name
    """
    teams = database.query(teams_sql, (league_id, year))

    return jsonify({
        "league": league[0],
        "teams": teams
    })


@api_bp.route("/leagues/<int:league_id>/seasons")
def league_seasons(league_id):
    league_sql = """
        SELECT LeagueID, Name, Country, LogoURL
        FROM League
        WHERE LeagueID = ?
    """
    league = database.query(league_sql, (league_id,))

    if not league:
        return jsonify({"error": "League not found"}), 404

    seasons_sql = """
        SELECT
            Year,
            StartDate,
            EndDate,
            Current
        FROM Seasons
        WHERE LeagueID = ?
        ORDER BY Year DESC
    """
    seasons = database.query(seasons_sql, (league_id,))

    return jsonify({
        "league": league[0],
        "seasons": seasons,
    })


@api_bp.route("/leagues/<int:league_id>/seasons/<int:year>")
def league_standings(league_id, year):
    league_sql = """
        SELECT
            l.LeagueID,
            l.Name,
            l.Country,
            l.LogoURL,
            s.Year,
            s.Current
        FROM League l
        LEFT JOIN Seasons s
            ON l.LeagueID = s.LeagueID
           AND s.Year = ?
        WHERE l.LeagueID = ?
    """
    league = database.query(league_sql, (year, league_id))

    if not league:
        return jsonify({"error": "League not found"}), 404

    sync_standings(league_id=league_id, season=year)

    standings_sql = """
        SELECT

            lt.Year,
            lt.TeamID,
            t.Name AS TeamName,
            t.Abbreviation AS TeamAbbreviation,
            t.LogoURL AS TeamLogoURL,
            lt.Position,
            lt.Description,
            lt.Points,
            lt.Played,
            lt.Won,
            lt.Drawn,
            lt.Lost,
            lt.GF,
            lt.GA,
            (lt.GF - lt.GA) AS GD
        FROM LeagueTable lt
        JOIN League l
            ON lt.LeagueID = l.LeagueID
        JOIN Teams t
            ON lt.TeamID = t.TeamID
        WHERE lt.LeagueID = ?
          AND lt.Year = ?
        ORDER BY lt.Position ASC, t.Name ASC
    """
    standings = database.query(standings_sql, (league_id, year))

    return jsonify({
        "league": league[0],
        "standings": standings,
    })


@api_bp.route("/leagues/<int:league_id>/seasons/<int:year>/recent-fixtures")
def league_recent_fixtures(league_id, year):
    page_param = request.args.get("page")
    per_page_param = request.args.get("per_page")
    page = 1
    per_page = 5

    try:
        if page_param is not None:
            page = int(page_param)
        if per_page_param is not None:
            per_page = int(per_page_param)
    except ValueError:
        return jsonify({
            "error": "page and per_page must be integers."
        }), 400

    if page < 1 or per_page < 1:
        return jsonify({
            "error": "page and per_page must be greater than 0."
        }), 400

    per_page = min(per_page, 50)
    league_sql = """
        SELECT
            l.LeagueID,
            l.Name,
            l.Country,
            l.LogoURL,
            s.Year,
            s.Current
        FROM League l
        LEFT JOIN Seasons s
            ON l.LeagueID = s.LeagueID
           AND s.Year = ?
        WHERE l.LeagueID = ?
    """
    league = database.query(league_sql, (year, league_id))

    if not league:
        return jsonify({"error": "League not found"}), 404

    sync_teams(league_id=league_id, season=year)
    sync_fixtures(league_id=league_id, season=year)

    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recent_fixtures, pagination = _get_paginated_recent_fixtures_for_league_season(
        league_id,
        year,
        page=page,
        per_page=per_page,
        match_date_before=current_timestamp,
    )

    return jsonify({
        "league": league[0],
        "recent_fixtures": recent_fixtures,
        "pagination": pagination,
    })


@api_bp.route("/fixtures")
def fixtures():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page_param = request.args.get("page")
    per_page_param = request.args.get("per_page")
    country_param = request.args.get("country")
    include_country_options = _is_truthy_query_param(request.args.get("include_country_options"))
    live_only = _is_truthy_query_param(request.args.get("live"))
    finished_only = _is_truthy_query_param(request.args.get("finished"))

    parsed_start = None
    parsed_end = None
    paginated_request = page_param is not None or per_page_param is not None
    page = 1
    per_page = 10
    normalized_country = _normalize_country_filter(country_param)

    try:
        if start_date:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({
            "error": "Invalid date format. Use YYYY-MM-DD for start_date and end_date."
        }), 400

    if paginated_request:
        try:
            if page_param is not None:
                page = int(page_param)
            if per_page_param is not None:
                per_page = int(per_page_param)
        except ValueError:
            return jsonify({
                "error": "page and per_page must be integers."
            }), 400

        if page < 1 or per_page < 1:
            return jsonify({
                "error": "page and per_page must be greater than 0."
            }), 400

        per_page = min(per_page, 50)

    if parsed_start and parsed_end and parsed_start > parsed_end:
        return jsonify({
            "error": "start_date cannot be later than end_date."
        }), 400

    if live_only and finished_only:
        return jsonify({
            "error": "live and finished filters cannot be used together."
        }), 400

    from_sql = """
        FROM Fixtures f
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
    """
    conditions = []
    params = []
    country_option_conditions = []
    country_option_params = []

    if parsed_start:
        conditions.append("DATE(f.MatchDate) >= DATE(?)")
        params.append(parsed_start.isoformat())
        country_option_conditions.append("DATE(f.MatchDate) >= DATE(?)")
        country_option_params.append(parsed_start.isoformat())

    if parsed_end:
        conditions.append("DATE(f.MatchDate) <= DATE(?)")
        params.append(parsed_end.isoformat())
        country_option_conditions.append("DATE(f.MatchDate) <= DATE(?)")
        country_option_params.append(parsed_end.isoformat())

    if live_only:
        live_status_placeholders = ", ".join("?" for _ in LIVE_STATUSES)
        live_status_condition = f"f.Status IN ({live_status_placeholders})"
        conditions.append(live_status_condition)
        params.extend(LIVE_STATUSES)
        country_option_conditions.append(live_status_condition)
        country_option_params.extend(LIVE_STATUSES)

    if finished_only:
        finished_status_placeholders = ", ".join("?" for _ in FINISHED_STATUSES)
        finished_status_condition = f"f.Status IN ({finished_status_placeholders})"
        conditions.append(finished_status_condition)
        params.extend(FINISHED_STATUSES)
        country_option_conditions.append(finished_status_condition)
        country_option_params.extend(FINISHED_STATUSES)

    if normalized_country:
        conditions.append("LOWER(l.Country) = LOWER(?)")
        params.append(normalized_country)

    where_sql = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    country_option_where_sql = (
        f" WHERE {' AND '.join(country_option_conditions)}"
        if country_option_conditions
        else ""
    )

    select_sql = f"""
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            l.Country AS Country,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            ht.LogoURL AS HomeTeamLogoURL,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
            at.LogoURL AS AwayTeamLogoURL,
            f.Location,
            f.MatchDate,
            f.HomeScore,
            f.AwayScore,
            f.Status,
            f.Elapsed
        {from_sql}
        {where_sql}
        ORDER BY f.MatchDate DESC
    """
    count_sql = f"""
        SELECT COUNT(*) AS TotalFixtures
        {from_sql}
        {where_sql}
    """
    country_options_sql = f"""
        SELECT DISTINCT l.Country AS Country
        {from_sql}
        {country_option_where_sql}
        ORDER BY l.Country ASC
    """

    if paginated_request:
        offset = (page - 1) * per_page
        select_sql += " LIMIT ? OFFSET ?"
        select_params = [*params, per_page, offset]
    elif not parsed_start and not parsed_end:
        select_sql += " LIMIT 10"
        select_params = params
    else:
        select_params = params

    fixtures = database.query(select_sql, tuple(select_params))

    if not paginated_request:
        return jsonify(fixtures)

    total_count_row = database.query(count_sql, tuple(params))
    total_fixtures = total_count_row[0]["TotalFixtures"] if total_count_row else 0
    total_pages = max(1, (total_fixtures + per_page - 1) // per_page)
    payload = {
        "fixtures": fixtures,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_fixtures": total_fixtures,
            "total_pages": total_pages,
            "has_previous": page > 1,
            "has_next": page < total_pages,
        }
    }

    if include_country_options:
        country_rows = database.query(country_options_sql, tuple(country_option_params))
        payload["countries"] = [row["Country"] for row in country_rows if row.get("Country")]

    return jsonify(payload)


@api_bp.route("/teams/<int:team_id>")
def team(team_id):
    recent_page_param = request.args.get("recent_page")
    recent_per_page_param = request.args.get("recent_per_page")
    recent_page = 1
    recent_per_page = 5

    try:
        if recent_page_param is not None:
            recent_page = int(recent_page_param)
        if recent_per_page_param is not None:
            recent_per_page = int(recent_per_page_param)
    except ValueError:
        return jsonify({
            "error": "recent_page and recent_per_page must be integers."
        }), 400

    if recent_page < 1 or recent_per_page < 1:
        return jsonify({
            "error": "recent_page and recent_per_page must be greater than 0."
        }), 400

    recent_per_page = min(recent_per_page, 50)
    team_data = _get_team(team_id)

    if not team_data:
        return jsonify({"error": "Team not found"}), 404

    statistics_context = _get_team_statistics_context(team_id)
    if statistics_context:
        sync_team_statistics(
            league_id=statistics_context["LeagueID"],
            season=statistics_context["Year"],
            team_id=team_id,
        )

    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    statistics_row = _get_team_statistics_row(team_id)
    upcoming_fixtures = _get_fixtures_for_team_ids(
        [team_id],
        limit=1,
        match_date_after=current_timestamp,
        order="ASC",
    )
    recent_fixtures, recent_fixtures_pagination = _get_paginated_fixtures_for_team_ids(
        [team_id],
        page=recent_page,
        per_page=recent_per_page,
        match_date_before=current_timestamp,
        order="DESC",
    )

    team_payload = {
        **team_data,
        "IsFavourite": _is_favourite_team(team_id),
        "Overview": (
            _build_team_overview(statistics_row)
            if statistics_row
            else None
        ),
        "StatisticsContext": (
            {
                "LeagueID": statistics_row["LeagueID"],
                "LeagueName": statistics_row["LeagueName"],
                "Year": statistics_row["Year"],
            }
            if statistics_row
            else None
        ),
    }

    return jsonify({
        "data": team_payload,
        "upcoming_fixture": upcoming_fixtures[0] if upcoming_fixtures else None,
        "recent_fixtures": recent_fixtures,
        "recent_fixtures_pagination": recent_fixtures_pagination,
    })


@api_bp.route("/fixtures/<int:fixture_id>")
def fixture(fixture_id):
    fixture_sql = """
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            ht.LogoURL AS HomeTeamLogoURL,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
            at.LogoURL AS AwayTeamLogoURL,
            f.Location,
            f.MatchDate,
            f.HomeScore,
            f.AwayScore,
            f.Status,
            f.Elapsed
        FROM Fixtures f
        JOIN League l
            ON f.LeagueID = l.LeagueID
        JOIN Teams ht
            ON f.HomeTeamID = ht.TeamID
        JOIN Teams at
            ON f.AwayTeamID = at.TeamID
        WHERE f.FixtureID = ?
    """

    fixture = database.query(fixture_sql, (fixture_id,))

    if not fixture:
        return jsonify({"error": "Fixture not found"}), 404

    fixture_data = fixture[0]

    sync_events(fixture_id)
    sync_fixture_statistics(fixture_id)
    sync_team_statistics(
        league_id=fixture_data["LeagueID"],
        season=fixture_data["Year"],
        team_id=fixture_data["HomeTeamID"],
    )
    sync_team_statistics(
        league_id=fixture_data["LeagueID"],
        season=fixture_data["Year"],
        team_id=fixture_data["AwayTeamID"],
    )

    events_sql = """
        SELECT
            e.FixtureID,
            e.EventID,
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
            e.ExtraMinute
        FROM Events e
        LEFT JOIN Teams t
            ON e.TeamID = t.TeamID
        WHERE e.FixtureID = ?
        ORDER BY e.EventMinute ASC, e.ExtraMinute ASC, e.EventID ASC
    """
    events = database.query(events_sql, (fixture_id,))
    event_vote_summaries = user_repo.get_event_vote_summaries(
        fixture_id,
        user_id=current_user.id if getattr(current_user, "is_authenticated", False) else None,
    )
    for event in events:
        vote_summary = event_vote_summaries.get(
            (event["FixtureID"], event["EventID"]),
            {"likes": 0, "dislikes": 0, "user_vote": None},
        )
        event["Likes"] = vote_summary["likes"]
        event["Dislikes"] = vote_summary["dislikes"]
        event["UserVote"] = vote_summary["user_vote"]

    statistics_sql = """
        SELECT
            fs.FixtureID,
            fs.TeamID,
            t.Name AS TeamName,
            fs.ShotsOnGoal,
            fs.ShotsOffGoal,
            fs.TotalShots,
            fs.BlockedShots,
            fs.ShotsInsideBox,
            fs.ShotsOutsideBox,
            fs.Fouls,
            fs.CornerKicks,
            fs.Offsides,
            fs.BallPossession,
            fs.YellowCards,
            fs.RedCards,
            fs.GoalkeeperSaves,
            fs.TotalPasses,
            fs.PassesAccurate,
            fs.PassesPercentage,
            fs.ExpectedGoals,
            fs.GoalsPrevented
        FROM FixtureStatistics fs
        JOIN Teams t
            ON fs.TeamID = t.TeamID
        WHERE fs.FixtureID = ?
        ORDER BY fs.TeamID ASC
    """
    statistics = database.query(statistics_sql, (fixture_id,))

    team_statistics_sql = """
        SELECT
            ts.LeagueID,
            ts.Year,
            ts.TeamID,
            t.Name AS TeamName,
            ts.Form,
            ts.WinsHome,
            ts.WinsAway,
            ts.DrawsHome,
            ts.DrawsAway,
            ts.LossesHome,
            ts.LossesAway,
            ts.GoalsForAverageHome,
            ts.GoalsForAverageAway,
            ts.GoalsAgainstAverageHome,
            ts.GoalsAgainstAverageAway,
            ts.FailedToScoreHome,
            ts.FailedToScoreAway
        FROM TeamStatistics ts
        JOIN Teams t
            ON ts.TeamID = t.TeamID
        WHERE ts.LeagueID = ?
          AND ts.Year = ?
          AND ts.TeamID IN (?, ?)
    """
    team_statistics_rows = database.query(
        team_statistics_sql,
        (
            fixture_data["LeagueID"],
            fixture_data["Year"],
            fixture_data["HomeTeamID"],
            fixture_data["AwayTeamID"],
        ),
    )
    team_statistics_by_id = {
        row["TeamID"]: row for row in team_statistics_rows
    }

    location_team_statistics = []

    home_team_stats = team_statistics_by_id.get(fixture_data["HomeTeamID"])
    if home_team_stats:
        location_team_statistics.append(
            {
                "TeamID": fixture_data["HomeTeamID"],
                "TeamName": fixture_data["HomeTeam"],
                "Venue": "home",
                "Values": _build_location_stats(home_team_stats, "home"),
            }
        )

    away_team_stats = team_statistics_by_id.get(fixture_data["AwayTeamID"])
    if away_team_stats:
        location_team_statistics.append(
            {
                "TeamID": fixture_data["AwayTeamID"],
                "TeamName": fixture_data["AwayTeam"],
                "Venue": "away",
                "Values": _build_location_stats(away_team_stats, "away"),
            }
        )

    h2h = {
        "home_vs_away": _get_h2h_fixtures(
            home_team_id=fixture_data["HomeTeamID"],
            away_team_id=fixture_data["AwayTeamID"],
            excluded_fixture_id=fixture_id,
        ),
        "away_vs_home": _get_h2h_fixtures(
            home_team_id=fixture_data["AwayTeamID"],
            away_team_id=fixture_data["HomeTeamID"],
            excluded_fixture_id=fixture_id,
        ),
    }

    return jsonify({
        "data": fixture,
        "events": events,
        "statistics": statistics,
        "team_location_statistics": location_team_statistics,
        "h2h": h2h,
    })
