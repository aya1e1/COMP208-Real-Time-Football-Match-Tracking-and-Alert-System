from flask import Blueprint, render_template

# create blueprint
main = Blueprint("main", __name__)

# homepage
@main.route("/")
def home():
    return render_template("home.html")

# live matches page
@main.route("/live")
def live():
    return render_template("live.html")