from datetime import datetime

from flask import Blueprint, jsonify, request
from backend.db import database
from backend.main import sync_events, sync_fixture_statistics, sync_team_statistics

api_bp = Blueprint("api", __name__)


def _last_five_form_chars(form: str | None) -> str:
    if not form:
        return ""
    return form[-5:]


def _build_location_stats(team_stats: dict, venue: str) -> dict:
    is_home = venue == "home"

    wins = team_stats["WinsHome"] if is_home else team_stats["WinsAway"]
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
        "losses": losses,
        "goals_for_average": goals_for_average,
        "goals_against_average": goals_against_average,
        "failed_to_score": failed_to_score,
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


@api_bp.route("/leagues")
def leagues():
    sql = """
        SELECT LeagueID, Name
        FROM League
        ORDER BY Name
    """
    leagues = database.query(sql)
    return jsonify(leagues)


@api_bp.route("/leagues/<int:league_id>/teams")
def league_teams(league_id):

    league_sql = """
        SELECT LeagueID, Name
        FROM League
        WHERE LeagueID = ?
    """
    league = database.query(league_sql, (league_id,))

    if not league:
        return jsonify({"error": "League not found"}), 404

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
        ORDER BY t.Name
    """
    teams = database.query(teams_sql, (league_id,))

    return jsonify({
        "league": league[0],
        "teams": teams
    })


@api_bp.route("/fixtures")
def fixtures():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    parsed_start = None
    parsed_end = None

    try:
        if start_date:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({
            "error": "Invalid date format. Use YYYY-MM-DD for start_date and end_date."
        }), 400

    if parsed_start and parsed_end and parsed_start > parsed_end:
        return jsonify({
            "error": "start_date cannot be later than end_date."
        }), 400

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
        WHERE 1 = 1
    """
    params = []

    if parsed_start:
        sql += " AND DATE(f.MatchDate) >= DATE(?)"
        params.append(parsed_start.isoformat())

    if parsed_end:
        sql += " AND DATE(f.MatchDate) <= DATE(?)"
        params.append(parsed_end.isoformat())

    sql += " ORDER BY f.MatchDate DESC"

    if not parsed_start and not parsed_end:
        sql += " LIMIT 10"

    fixtures = database.query(sql, tuple(params))
    return jsonify(fixtures)


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
