from flask import Blueprint, make_response, render_template, redirect, send_file, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from src import db
from src.utils.decorators import check_is_confirmed
from src.accounts.models import Attendance, Status, User
from qrcode import QRCode, ERROR_CORRECT_L
import io
from qrcode.constants import ERROR_CORRECT_L
import os
from qrcode import make
from PIL import Image

core_bp = Blueprint("core", __name__)

@core_bp.route("/")
@login_required
@check_is_confirmed
def home():
    user = current_user

    if user.is_faculty:
        return render_template("core/faculty/index.html")
    else:
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

        return render_template("core/student/index.html")
    
#################
# FACULTY VIEWS
#################

@core_bp.route("/realtime")
@login_required
@check_is_confirmed
def realtime():
    attendance_records = Attendance.query.order_by(Attendance.created.desc()).all()
    attendance_user = db.session.query(User).join(Attendance, User.id == Attendance.user_id).all()

    return render_template("core/faculty/realtime.html", attendance_records=attendance_records, attendance_user=attendance_user, zip=zip)

@core_bp.route('/records')
@login_required
@check_is_confirmed
def records():
    students = db.session.query(User).filter(User.is_faculty==False).order_by(User.last_name.asc()).all()

    return render_template('core/faculty/records.html', students=students)

@core_bp.route('/classlist')
@login_required
@check_is_confirmed
def classlist():
    return render_template('core/faculty/classlist.html')



#################
# STUDENT VIEWS
#################

@core_bp.route('/show_qrcode')
@login_required
@check_is_confirmed
def show_qrcode():
    return render_template("core/student/qrcode.html")

@core_bp.route('/view_qr_code')
@login_required
@check_is_confirmed
def view_qr_code():
    user = current_user

    if user.qr_code:
        # Construct the absolute file path for the user's QR code image
        user_id = user.id  # Assuming user.id is the user's ID
        file_path = os.path.join(os.getcwd(), 'student_qrcode', f"{user_id}_qr_code.png")

        # Check if the file exists
        if os.path.isfile(file_path):
            print(f"File found: {file_path}")  # Add this line for debugging
            # Serve the QR code image directly
            return send_file(file_path, mimetype='image/png')
        else:
            # Handle the case where the QR code file doesn't exist
            print(f"File not found: {file_path}")  # Add this line for debugging
            return "QR code not found", 404

    # Handle the case where the user doesn't have a QR code
    return "QR code not found", 404

@core_bp.route('/download_qr_code')
@login_required
@check_is_confirmed
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