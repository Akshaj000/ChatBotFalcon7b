from flask import request, render_template, redirect, url_for, Blueprint
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from models import User
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password").strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template("register.html"), 401
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home.home"))
    return render_template("login.html"), 401


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    from app import db
    from models import User
    if request.method == "POST":
        email = request.form.get("email")
        users = User.query.filter_by(email=email)
        if users.count() > 0:
            return redirect(url_for("auth.login"))
        password = request.form.get("password")
        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth_bp.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login")), 200


__all__ = [
    "auth_bp"
]
