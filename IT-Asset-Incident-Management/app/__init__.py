from datetime import timezone
from zoneinfo import ZoneInfo
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(test_config=None):
    app = Flask(__name__)
    @app.template_filter("ist")
    def format_ist(value, fmt="%d %b %Y, %I:%M %p"):
        if not value:
            return "-"

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.astimezone(
            ZoneInfo("Asia/Kolkata")
        ).strftime(fmt)

    app.config.from_object("config.Config")
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        from app import models

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return db.session.get(User, int(user_id))