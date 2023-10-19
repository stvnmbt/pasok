from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app, Response, send_file, make_response
from flask_login import current_user, login_required, login_user, logout_user

from src import bcrypt, db
from src.accounts.models import User
from src.accounts.token import confirm_token, generate_token
from src.utils.decorators import logout_required
from src.utils.email import send_email

from qrcode import QRCode, ERROR_CORRECT_L

import io

from qrcode.constants import ERROR_CORRECT_L
from qrcode import make
from PIL import Image
#import base64  # accessing base64 module
#import os
import logging
from .forms import LoginForm, RegisterForm

logger = logging.getLogger("accounts_bp")
logger.setLevel(logging.INFO)

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

        # Generate and save the QR code for the user
        generate_and_save_qr_code(user)

        db.session.commit()


        # Send confirmation email with QR code
        token = generate_token(user.email)
        confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
        html = render_template("accounts/confirm_email.html", confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        login_user(user)

        flash("A confirmation email has been sent via email.", "success")
        return redirect(url_for("accounts.inactive"))

    return render_template("accounts/register.html", form=form)



def generate_and_save_qr_code(user):
    qr = QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Check if user.id is not None before concatenating
    if user.id is not None:
        qr_data = f"{user.id}{user.first_name}{user.last_name}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_code_image = qr.make_image(fill_color="black", back_color="white")

        # Convert the QR code image to bytes
        qr_code_bytes = io.BytesIO()
        qr_code_image.save(qr_code_bytes, format='PNG')
        qr_code_bytes = qr_code_bytes.getvalue()

        # Store the QR code bytes in the user's record
        user.qr_code = qr_code_bytes
        db.session.commit()


@accounts_bp.route("/login", methods=["GET", "POST"])
@logout_required
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("core.home"))
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
    if current_user.is_confirmed:
        flash("Account already confirmed.", "success")
        return redirect(url_for("core.home"))
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
    return redirect(url_for("core.home"))





#put this sa core

@accounts_bp.route('/view_qr_code')
@login_required
def view_qr_code():
    user = current_user

    # Check if the user has a QR code
    if user.qr_code:
        # Render the HTML template and pass the QR code file path
        return render_template('core/qr_code.html', qr_code_path=user.qr_code)

    # Handle the case where the user doesn't have a QR code
    return "QR code not found", 404


@accounts_bp.route('/download_qr_code')
@login_required
def download_qr_code():
    user = current_user

    # Check if the user has a QR code
    if user.qr_code:
        # Get the QR code bytes from the user object
        qr_code_bytes = user.qr_code

        # Create a response object with the QR code data
        response = make_response(qr_code_bytes)

        # Set the appropriate headers for the response
        response.headers.set('Content-Type', 'image/png')

        # Set the filename as the first name and last name of the user
        filename = f"{user.first_name}_{user.last_name}_qr_code.png"
        response.headers.set('Content-Disposition', 'attachment', filename=filename)

        return response
        
    # Handle the case where the user doesn't have a QR code
    return "QR code not found", 404


@accounts_bp.route("/inactive")
@login_required
def inactive():
    if current_user.is_confirmed:
        return redirect(url_for("core.home"))
    return render_template("accounts/inactive.html")


@accounts_bp.route("/resend")
@login_required
def resend_confirmation():
    if current_user.is_confirmed:
        flash("Your account has already been confirmed.", "success")
        return redirect(url_for("core.home"))
    token = generate_token(current_user.email)
    confirm_url = url_for("accounts.confirm_email", token=token, _external=True)
    html = render_template("accounts/confirm_email.html", confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash("A new confirmation email has been sent.", "success")
    return redirect(url_for("accounts.inactive"))
