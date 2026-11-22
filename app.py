import os

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

from config import Config, database_url
from users.users.models import User, db
from webapp.routes import routes_bp

app = Flask(
    __name__,
    static_url_path="/webapp/static",
    static_folder="webapp/static",
    template_folder="webapp/templates",
)
app.config.from_object(Config)

secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    if os.environ.get("FLASK_ENV") == "production":
        raise ValueError(
            "FLASK_SECRET_KEY environment variable must be set in production"
        )
    secret_key = "dev-only-insecure-key"
app.secret_key = secret_key

app.config["SQLALCHEMY_DATABASE_URI"] = database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

mail = Mail()
mail.init_app(app)

db.init_app(app)
migrate = Migrate(app, db)

# Minimal Flask-Login setup (needed for login_user/logout_user)
login_manager = LoginManager(app)
login_manager.login_view = "routes.signin"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(routes_bp)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response
