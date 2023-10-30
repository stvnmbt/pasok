from flask import Blueprint, make_response, render_template, redirect, send_file, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from src import db
from src.utils.decorators import check_is_confirmed
from src.accounts.models import Attendance, Status
from qrcode import QRCode, ERROR_CORRECT_L
import io
from qrcode.constants import ERROR_CORRECT_L
from qrcode import make
from PIL import Image
import os

core_bp = Blueprint("core", __name__)

@core_bp.route("/")
@login_required
@check_is_confirmed
def home_faculty():
    attendance_records = Attendance.query.order_by(Attendance.created.desc())
    return render_template("core/faculty/index.html", attendance_records=attendance_records)

@core_bp.route("/")
@login_required
@check_is_confirmed
def home_student():
    attendance_records = Attendance.query.order_by(Attendance.created.desc())
    return render_template("core/student/index.html", attendance_records=attendance_records)

@core_bp.route("/add", methods=["GET", "POST"])
@login_required
@check_is_confirmed
def add():
    if request.form.get("add_attendance"):
        # Handle the form submit (button click) to add attendance
        attendance = Attendance(attendance_status=Status.PRESENT, user_id=current_user.id)
        db.session.add(attendance)
        db.session.commit()
        flash("Attendance added successfully!")

    if request.is_json:
        # Handle the POST request from the QR code scanner to add attendance
        data = request.get_json()
        user_id = data.get("user_id")
        if user_id is not None:
            attendance = Attendance(attendance_status=Status.PRESENT, user_id=user_id)
            db.session.add(attendance)
            db.session.commit()
            return jsonify({"message": "Attendance added successfully"})
        
    attendance_records = Attendance.query.order_by(Attendance.created.desc()).all()
    return render_template("core/faculty/index.html", attendance_records=attendance_records)

@core_bp.route('/view_qr_code')
@login_required
def view_qr_code():
    user = current_user

    # Check if the user has a QR code; if not, generate one
    if not user.qr_code:
        # Generate the QR code
        qr = QRCode(
            version=1,
            error_correction=ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_data = user.id

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

        # Determine the folder where you want to save the QR code
        save_folder = 'student_qrcode'

        # Create the folder if it doesn't exist
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # Define the file path for the QR code image
        file_path = os.path.join(save_folder, f"{user.id}_qr_code.png")

        # Save the QR code image as a file
        qr_code_image.save(file_path, format='PNG')

        # Serve the QR code image directly
        return send_file(file_path, mimetype='image/png')

    # If the user already has a QR code, serve the existing QR code
    return send_file(io.BytesIO(user.qr_code), mimetype='image/png')


@core_bp.route('/download_qr_code')
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