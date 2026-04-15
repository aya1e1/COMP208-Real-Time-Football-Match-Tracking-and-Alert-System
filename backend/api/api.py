from flask import Blueprint, jsonify
from backend.db import database

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
