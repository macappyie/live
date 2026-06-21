from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, bcrypt
from models import User

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect("/dashboard")

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and Password are required.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()

        if user is None:
            flash("User not found.", "danger")
            return render_template("login.html")

        if not bcrypt.check_password_hash(user.password, password):
            flash("Invalid password.", "danger")
            return render_template("login.html")

        if not user.is_active:
            flash("Your account has been disabled.", "danger")
            return render_template("login.html")

       # login_user(user)
        login_user(user)
# Admin login
        if user.is_admin:
            return redirect("/admin")

# User ne payment nahi kiya
        if not user.is_paid:
            return redirect("/payment")

# Payment ho gaya
        return redirect("/dashboard")

        # Payment check baad me enable karenge
        # if not user.is_paid:
        #     return redirect("/payment")

       # return redirect("/dashboard")

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect("/dashboard")

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")

        if not full_name or not email or not mobile or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        existing = User.query.filter_by(email=email).first()

        if existing:
            flash("Email already registered.", "danger")
            return render_template("register.html")

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(
            full_name=full_name,
            email=email,
            mobile=mobile,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")

        return redirect("/login")
    return render_template("register.html")

@auth.route("/forgot-password", methods=["GET","POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email","").strip().lower()

        user = User.query.filter_by(email=email).first()

        if not user:

            flash("Email not found.","danger")
            return render_template("forgot_password.html")

        return redirect(url_for("auth.reset_password", user_id=user.id))

        return render_template("forgot_password.html")


@auth.route("/reset-password/<int:user_id>", methods=["GET","POST"])
def reset_password(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == "POST":

        password = request.form.get("password")

        confirm = request.form.get("confirm")

        if password != confirm:

            flash("Passwords do not match.","danger")

            return render_template("reset_password.html")

        user.password = bcrypt.generate_password_hash(password).decode("utf-8")

        db.session.commit()

        flash("Password Updated Successfully","success")

        return redirect("/login")

    return render_template("reset_password.html")

   # return render_template("register.html")


@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect("/login")
