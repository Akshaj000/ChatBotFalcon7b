from flask import render_template, Blueprint
from flask_login import login_required
from .llm import llm_bp
from .auth import auth_bp

home_bp = Blueprint('home', __name__)


@home_bp.route("/")
@login_required
def home():
    return render_template("index.html")


__all__ = [
    "home_bp",
    "llm_bp",
    "auth_bp"
]
