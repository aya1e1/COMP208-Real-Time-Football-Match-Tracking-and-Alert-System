"""app.py: Flask application factory."""
import os
from flask import Flask
from backend.db.database import init_db


def create_app():
    """Create and configure the Flask application.
    Initialises the database and registers all route blueprints.
    Returns the configured Flask app instance.
    """
    # Create Flask app, pointing to frontend folders for templates and static files
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )

    # Secret key used by Flask to secure user sessions (login cookies)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # Initialise the database - creates all tables if they don't exist
    init_db()

    # Import and register all route blueprints
    from backend.routes.main          import main_bp
    from backend.routes.fixtures      import fixtures_bp
    from backend.routes.teams         import teams_bp
    from backend.routes.players       import players_bp
    from backend.routes.auth          import auth_bp
    from backend.routes.notifications import notif_bp

    # Register each blueprint with its URL prefix
    app.register_blueprint(main_bp)                              # /
    app.register_blueprint(fixtures_bp,  url_prefix="/fixtures") # /fixtures/...
    app.register_blueprint(teams_bp,     url_prefix="/teams")    # /teams/...
    app.register_blueprint(players_bp,   url_prefix="/players")  # /players/...
    app.register_blueprint(auth_bp,      url_prefix="/auth")     # /auth/...
    app.register_blueprint(notif_bp,     url_prefix="/notifications") # /notifications/...

    return app