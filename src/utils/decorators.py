from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

def check_is_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_confirmed is False and current_user.is_faculty is True:
            flash("Please confirm your account!", "warning")
            return redirect(url_for("accounts.inactive"))
        return func(*args, **kwargs)

    return decorated_function

def logout_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash("You are already authenticated.", "info")
            return redirect(url_for("core.home"))
        return func(*args, **kwargs)

    return decorated_function

def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_faculty:
            return func(*args, **kwargs)
        else:
            flash("You are not authorized to access this page.", "warning")
            return redirect(url_for('core.home'))
    return decorated_function

def student_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_faculty:
            return func(*args, **kwargs)
        else:
            flash("You are not authorized to access this page.", "warning")
            return redirect(url_for('core.home'))
    return decorated_function