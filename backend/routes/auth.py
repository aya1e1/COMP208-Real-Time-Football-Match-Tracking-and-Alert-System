from flask import Blueprint, render_template, request

auth = Blueprint("auth", __name__)

# log in page
@auth.route("/login")
def login_page():
    return render_template("login.html")

# log in action
@auth.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    print(username, password) #debug

    return render_template("dashboard.html")

# register page
@auth.route("/register")
def register_page():
  return render_template("register.html")



