"""
Flask-Login integration for ResearchAI user authentication.
"""

from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from functools import wraps

from database import get_user_by_id, verify_user

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to use ResearchAI."


class User(UserMixin):
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username


@login_manager.user_loader
def load_user(user_id: str):
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return None

    user = get_user_by_id(user_id_int)
    if user:
        return User(user["id"], user["username"])
    return None


def init_auth(app: Flask) -> None:
    login_manager.init_app(app)


def authenticate(username: str, password: str):
    user = verify_user(username, password)
    if not user:
        return None
    return User(user["id"], user["username"])


def login_required_view(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated
