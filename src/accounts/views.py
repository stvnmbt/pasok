from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from src import bcrypt, db
from src.accounts.models import User
from src.accounts.token import confirm_token, generate_token
from src.utils.decorators import logout_required
from src.utils.email import send_email

#import base64  # accessing base64 module
#import os
import logging
from .forms import LoginForm, RegisterForm

logger = logging.getLogger("accounts_bp")
logger.setLevel(logging.INFO)

import re

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/register", methods=["GET", "POST"])
@logout_required
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            last_name=form.last_name.data,
        )
        
        db.session.add(user)

        # Assign faculty role if email domain is valid
        email_domain = re.search(r"@(.*)$", user.email)
        if email_domain.group(0) == "@inboxkitten.com": # change to "@pup.edu.ph" in production
            user.is_faculty = True
        
        db.session.commit()

        # Send confirmation email
        token = generate_token(user.email)
        confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
        html = render_template("accounts/confirm_email.html", confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        login_user(user)

        flash("A confirmation email has been sent via email.", "success")

        return redirect(url_for("accounts.inactive"))

    return render_template("accounts/register.html", form=form)

@accounts_bp.route("/login", methods=["GET", "POST"])
@logout_required
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]) and user.is_faculty:
            login_user(user)
            return redirect(url_for("core.home_faculty"))
        elif user and bcrypt.check_password_hash(user.password, request.form["password"]) and not user.is_faculty:
            login_user(user)
            return redirect(url_for("core.home_student"))
        else:
            flash("Invalid email and/or password.", "danger")
            return render_template("accounts/login.html", form=form)
    return render_template("accounts/login.html", form=form)


@accounts_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You were logged out.", "success")
    return redirect(url_for("accounts.login"))


@accounts_bp.route("/confirm/<token>")
@login_required
def confirm_email(token):
    if current_user.is_confirmed and current_user.is_faculty:
        flash("Account already confirmed.", "success")
        return redirect(url_for("core.home_faculty"))
    elif current_user.is_confirmed and not current_user.is_faculty:
        flash("Account already confirmed.", "success")
        return redirect(url_for("core.home_student"))

    email = confirm_token(token)
    user = User.query.filter_by(email=current_user.email).first_or_404()
    if user.email == email:
        user.is_confirmed = True
        user.confirmed_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash("You have confirmed your account. Thanks!", "success")
    else:
        flash("The confirmation link is invalid or has expired.", "danger")
    if current_user.is_faculty:
        return redirect(url_for("core.home_faculty"))
    elif not current_user.is_faculty:
        return redirect(url_for("core.home_student"))

@accounts_bp.route("/inactive")
@login_required
def inactive():
    if current_user.is_confirmed and current_user.is_faculty:
        return redirect(url_for("core.home_faculty"))
    elif current_user.is_confirmed and not current_user.is_faculty:
        return redirect(url_for("core.home_student"))
    return render_template("accounts/inactive.html")


@accounts_bp.route("/resend")
@login_required
def resend_confirmation():
    if current_user.is_confirmed and current_user.is_faculty:
        flash("Your account has already been confirmed. Thank you!", "success")
        return redirect(url_for("core.home_faculty"))
    elif current_user.is_confirmed and not current_user.is_faculty:
        flash("Your account has already been confirmed. Thank you!", "success")
        return redirect(url_for("core.home_student"))
    token = generate_token(current_user.email)
    confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
    html = render_template("accounts/confirm_email.html", confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash("A new confirmation email has been sent.", "success")
    return redirect(url_for("accounts.inactive"))
