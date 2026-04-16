from flask import Blueprint, abort, render_template

teams_bp = Blueprint("teams", __name__)


@teams_bp.route("/")
def show_teams():
    abort(404)


@teams_bp.route("/<int:team_id>")
def team(team_id):
    return render_template("team.html", team_id=team_id)
