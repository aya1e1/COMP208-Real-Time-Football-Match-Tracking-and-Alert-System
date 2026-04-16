from flask import Blueprint, render_template

leagues_bp = Blueprint("leagues", __name__)


@leagues_bp.route("/<int:league_id>")
def league(league_id):
    return render_template("league.html", league_id=league_id)
