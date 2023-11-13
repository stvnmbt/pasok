from datetime import datetime
from flask import Blueprint, make_response, render_template, request, send_file
from flask_login import login_required, current_user
from src import db
from src.utils.decorators import check_is_confirmed
from src.accounts.models import Attendance, User
import qrcode
from qrcode.image.styledpil import StyledPilImage
import io
import os

from src.utils.scanner import add_attendance

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
            qr = qrcode.QRCode(
                version=5,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr_data = user.id
            qr.add_data(qr_data)
            qr_code_image = qr.make_image(image_factory=StyledPilImage, embeded_image_path="src\static\images\PUP logo white bg.png")

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
    attendance_user = db.session.query(Attendance)\
    .join(User, User.id == Attendance.user_id)\
    .add_columns(User.first_name, User.last_name, User.section_code, Attendance.created, Attendance.attendance_status)\
    .order_by(Attendance.created.desc())\
    .all()

    return render_template("core/faculty/realtime.html", attendance_user=attendance_user, zip=zip)

''' Di ko pa kayang i-let go haha halos buong araw ko to cinode comment ko muna
@core_bp.route("/update_table", methods=['GET'])
@login_required
@check_is_confirmed
def update_table():
    last_attendance = db.session.query(Attendance)\
    .join(User, User.id == Attendance.user_id)\
    .add_columns(User.first_name, User.last_name, User.section_code, Attendance.created, Attendance.attendance_status)\
    .order_by(Attendance.created.desc())\
    .first()

    return json.dumps(last_attendance, default=str)
    #return jsonify(last_attendance)
'''

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

@core_bp.route('/qrscanner')
@login_required
@check_is_confirmed
def qrscanner():
    return render_template('core/faculty/qrscanner.html')

@core_bp.route('/get_qr', methods=['POST'])
def get_qr():
    s = request.get_json()

    # anti duplicate measure
    #last_attendance = Attendance.query.order_by(Attendance.created.desc()).first()
    last_attendance = db.session.query(Attendance).filter(Attendance.user_id==s).order_by(Attendance.created.desc()).first()
    if last_attendance is None:
        add_attendance(s)
        return ('Success!', 200)
    else:
        time_now = datetime.now()
        time_last = (time_now-last_attendance.created).total_seconds()
        # str(last_attendance.user_id) != s and 
        if time_last > 60: # ADD: change duration later
            print(f'USERID {s}, TIMENOW {time_now}, LAST TIME {last_attendance.created}, TIMELAST {time_last}')
            add_attendance(s)
            return ('Success!', 200)
    return ('', 204)

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