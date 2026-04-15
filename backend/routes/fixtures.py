from flask import Blueprint, render_template

fixtures_bp = Blueprint("fixtures", __name__)


@fixtures_bp.route("/")
def show_fixtures():
    return render_template("live.html")


@fixtures_bp.route("/<int:fixture_id>")
def match(fixture_id):
    return render_template("fixture_view.html", match_id=fixture_id)
