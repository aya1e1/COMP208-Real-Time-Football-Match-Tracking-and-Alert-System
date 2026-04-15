from flask import Blueprint

notif_bp = Blueprint("notifications", __name__)


@notif_bp.route("/")
def notifications_home():
    return {"message": ""}
