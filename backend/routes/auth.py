from flask import Blueprint, render_template, request

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login_page():
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    print(username, password)

    return render_template("dashboard.html")


@auth_bp.route("/register")
def register_page():
    return render_template("register.html")
