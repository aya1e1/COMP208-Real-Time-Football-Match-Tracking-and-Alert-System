from flask import Blueprint, render_template

try:
    from flask_login import login_required
except ModuleNotFoundError:
    def login_required(func):
        return func

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/live")
def live():
    return render_template("live.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
