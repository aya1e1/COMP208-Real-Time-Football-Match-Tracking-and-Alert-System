"""app.py: Flask application factory."""
import os

from dotenv import load_dotenv
from flask import Flask

from backend.db.database import init_db
from backend.db.users import init_login_manager

load_dotenv()


def setup_data() -> None:

    from backend.data_sync import (
        USE_MOCKS,
        sync_events,
        sync_fixture_statistics,
        sync_fixtures,
        sync_leagues,
        sync_players,
        sync_team_statistics,
        sync_teams,
    )

    if USE_MOCKS:
        print("Using mock API responses")

    init_db()
    print("Database initialised")

    sync_leagues()
    sync_teams(league_id=39, season=2024)
    sync_fixtures(league_id=39, season=2024)
    sync_events(fixture_id=1208399)
    sync_fixture_statistics(fixture_id=1208399)
    sync_team_statistics(league_id=39, season=2024, team_id=41)
    sync_players(player_id=138908)


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
    init_login_manager(app)

    # Initialise the database and sync baseline data used by the app
    setup_data()

    # Import and register all route blueprints
    from backend.routes.main          import main_bp
    from backend.routes.fixtures      import fixtures_bp
    from backend.routes.teams         import teams_bp
    from backend.routes.players       import players_bp
    from backend.routes.auth          import auth_bp
    from backend.routes.notifications import notif_bp
    from backend.api.api              import api_bp

    # Register each blueprint with its URL prefix
    app.register_blueprint(main_bp)                              # /
    app.register_blueprint(fixtures_bp,  url_prefix="/fixtures") # /fixtures/...
    app.register_blueprint(teams_bp,     url_prefix="/teams")    # /teams/...
    app.register_blueprint(players_bp,   url_prefix="/players")  # /players/...
    app.register_blueprint(auth_bp,      url_prefix="/auth")     # /auth/...
    app.register_blueprint(notif_bp,     url_prefix="/notifications") # /notifications/...
    app.register_blueprint(api_bp,       url_prefix="/api")      # /api/...

    return app
