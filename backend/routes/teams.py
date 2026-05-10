from flask import Blueprint, render_template

teams_bp = Blueprint("teams", __name__)

# all teams page
@teams_bp.route("/")
def teams():
    return render_template("team.html")

# single team page
@teams_bp.route("/<int:id>")
def team_detail(id):
    return render_template("team.html", team_id=id)
