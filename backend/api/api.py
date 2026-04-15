from datetime import datetime

from flask import Blueprint, jsonify, request
from backend.db import database
from backend.main import sync_events, sync_fixture_statistics

api_bp = Blueprint("api", __name__)


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
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
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
    sync_events(fixture_id)
    sync_fixture_statistics(fixture_id)

    fixture_sql = """
        SELECT
            f.FixtureID,
            f.LeagueID,
            l.Name AS LeagueName,
            f.Year,
            f.HomeTeamID,
            ht.Name AS HomeTeam,
            ht.Abbreviation AS HomeTeamAbbreviation,
            f.AwayTeamID,
            at.Name AS AwayTeam,
            at.Abbreviation AS AwayTeamAbbreviation,
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

    return jsonify({
        "data": fixture,
        "events": events,
        "statistics": statistics,
    })
