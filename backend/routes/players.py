from flask import Blueprint, render_template

players_bp = Blueprint("players", __name__)

# all players page
@players_bp.route("/")
def players():
    return render_template("player.html")

# single player page
@players_bp.route("/<int:id>")
def player_detail(id):
    return render_template("player.html", player_id=id)