from flask import Blueprint, render_template

# create blueprint
teams = Blueprint("teams", __name__)

# display all football teams
@teams.route("/teams")
def show_teams():
  return render_template("teams.html")
