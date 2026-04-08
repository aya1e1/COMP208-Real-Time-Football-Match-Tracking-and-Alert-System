from flask import Blueprint, render_template

# create blueprint
fixtures = Blueprint("fixtures", __name__)

# all fixtures page
@fixtures.route("/fixtures")
def show_fixtures():
    return render_template("live.html")

# single match page
@fixtures.route("/match/<int:id>")
def match(id):
    return render_template("match.html", match_id=id)
