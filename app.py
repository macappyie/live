from flask import Flask, render_template, redirect
from itsdangerous import URLSafeTimedSerializer

from flask_login import login_required, current_user

from config import Config
from extensions import db, bcrypt, login_manager

# Blueprints
from auth import auth
from dashboard import dashboard
from payment import payment
from admin import admin


def create_app():

    app = Flask(__name__)

    # Configuration
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Blueprints
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(payment)
    app.register_blueprint(admin)

    # Create Database
    with app.app_context():
        from models import User
        db.create_all()

    # ---------------------------------
    # Home Page
    # ---------------------------------

    @app.route("/")
    def home():
        return render_template("home.html")

    # ---------------------------------
    # Secure Scanner
    # ---------------------------------

    @app.route("/open-scanner")
    @login_required
    def open_scanner():

        if not current_user.is_paid:
            return redirect("/payment")

        s = URLSafeTimedSerializer(app.config["SECRET_KEY"])

        token = s.dumps(
            {
                "user_id": current_user.id,
                "email": current_user.email
            }
        )

        return redirect(
            f"https://scanner.moneyassure.org/?token={token}"
        )

    return app


app = create_app()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5003,
        debug=True
    )
