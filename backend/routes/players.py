from flask import Blueprint, render_template

players_bp = Blueprint("players", __name__)


@players_bp.route("/")
def show_players():
    return render_template("player.html")
