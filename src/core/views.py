from flask import Blueprint, make_response, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from src import db
from src.utils.decorators import check_is_confirmed
from src.accounts.models import Attendance, Status
from qrcode import QRCode, ERROR_CORRECT_L
import io
from qrcode.constants import ERROR_CORRECT_L

core_bp = Blueprint("core", __name__)

@core_bp.route("/")
@login_required
@check_is_confirmed
def home():
    if current_user.is_faculty:
        return render_template("core/faculty/index.html")
    else:
        return render_template("core/student/index.html")

########################
# FACULTY VIEWS
########################

@core_bp.route("/realtime", methods=["GET", "POST"])
@login_required
@check_is_confirmed
def realtime():
    attendance_records = Attendance.query.order_by(Attendance.created.desc()).all()
    return render_template("core/faculty/realtime.html", attendance_records=attendance_records)

@core_bp.route('/records')
@login_required
@check_is_confirmed
def records():
    return render_template('core/faculty/records.html')

@core_bp.route('/classlist')
@login_required
@check_is_confirmed
def classlist():
    return render_template('core/faculty/classlist.html')



########################
# STUDENT VIEWS
########################

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

    # Render the HTML template and pass the QR code file path
    return render_template('core/student/qrcode.html', qr_code_path=user.qr_code)

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