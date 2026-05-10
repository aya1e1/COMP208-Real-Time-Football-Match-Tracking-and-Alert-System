from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from sqlite3 import IntegrityError

try:
    from flask_login import current_user, login_required, login_user, logout_user
except ModuleNotFoundError:
    def login_required(func):
        return func

    def login_user(user):
        return user

    def logout_user():
        return None

    class _AnonymousUser:
        is_authenticated = False

    current_user = _AnonymousUser()

from backend.db import users

auth_bp = Blueprint("auth", __name__)


def _request_value(name: str) -> str:
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        return (payload.get(name) or "").strip()
    return request.form.get(name, "").strip()


def _wants_json_response() -> bool:
    return request.is_json or request.path.startswith("/api/")


@auth_bp.route("/login")
def login_page():
    if getattr(current_user, "is_authenticated", False):
        return redirect(url_for("main.home"))
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    identifier = _request_value("username") or _request_value("email")
    password = _request_value("password")

    user = users.authenticate_user(identifier, password)
    if not user:
        if _wants_json_response():
            return jsonify({"error": "Invalid username/email or password"}), 401
        return render_template("login.html", error="Invalid username/email or password"), 401

    login_user(user)

    if _wants_json_response():
        return jsonify({"user": user.to_dict()})

    return redirect(url_for("main.home"))


@auth_bp.route("/register")
def register_page():
    if getattr(current_user, "is_authenticated", False):
        return redirect(url_for("main.home"))
    return render_template("register.html")


@auth_bp.route("/register", methods=["POST"])
def register():
    username = _request_value("username")
    email = _request_value("email")
    password = _request_value("password")

    if not username or not email or not password:
        error = {"error": "username, email, and password are required"}
        if _wants_json_response():
            return jsonify(error), 400
        return render_template("register.html", error=error["error"]), 400

    if len(username) < 3:
        error = {"error": "Username must be at least 3 characters"}
        if _wants_json_response():
            return jsonify(error), 400
        return render_template("register.html", error=error["error"]), 400

    try:
        user = users.create_user(username, email, password)
    except IntegrityError:
        error = {"error": "Username or email already exists"}
        if _wants_json_response():
            return jsonify(error), 409
        return render_template("register.html", error=error["error"]), 409

    login_user(user)

    if _wants_json_response():
        return jsonify({"user": user.to_dict()}), 201

    return redirect(url_for("main.home"))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()

    if _wants_json_response():
        return jsonify({"success": True})

    return redirect(url_for("main.home"))
