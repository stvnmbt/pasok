import base64
from datetime import datetime
import io
from flask import Blueprint, make_response, render_template, request, send_file, jsonify, Response
from flask_login import login_required, current_user
from src import db
from src.utils.decorators import admin_required, check_is_confirmed
from src.accounts.models import Attendance, User, ClassList
import os
import csv 
from io import StringIO
from src.utils.generate_qr import generate_qr
from src.utils.scanner import add_attendance
from collections import defaultdict

core_bp = Blueprint("core", __name__)

@core_bp.route("/")
@login_required
@check_is_confirmed
def home():
    user = current_user

    if user.is_faculty:
        return render_template("core/faculty/index.html")
    else:
        return render_template("core/student/index.html")
    
#################
# FACULTY VIEWS
#################

@core_bp.route("/realtime")
@login_required
@check_is_confirmed
@admin_required
def realtime():
    #attendance_user = db.session.query(Attendance)\
    attendance_user = Attendance.query\
    .join(User, User.id == Attendance.user_id)\
    .add_columns(User.first_name, User.last_name, User.section_code, Attendance.created, Attendance.attendance_status)\
    .order_by(Attendance.created.desc())\
    .all()

    return render_template("core/faculty/realtime.html", attendance_user=attendance_user, zip=zip)

@core_bp.route('/records')
@login_required
@check_is_confirmed
@admin_required
def records():
    #students = db.session.query(User).filter(User.is_faculty==False).order_by(User.last_name.asc()).all()
    students = User.query.filter(User.is_faculty==False).order_by(User.last_name.asc()).all()

    return render_template('core/faculty/records.html', students=students)

@core_bp.route('/classlist')
@login_required
@check_is_confirmed
@admin_required
def classlist():
    return render_template('core/faculty/classlist.html')

@core_bp.route("/export_classlist_attendance_csv/<int:classlist_id>", methods=["GET"])
@login_required
@check_is_confirmed
@admin_required
def export_classlist_attendance_csv(classlist_id):
    # Retrieve attendance records for the classlist
    classlist = ClassList.query.get(classlist_id)
    
    # Check if the user has permission to access this classlist
    if current_user.is_faculty and current_user != classlist.user_classlist:
        return jsonify({"error": "You don't have permission to access this classlist"}), 403

    attendance_records = (
        Attendance.query.join(User)
        .filter(Attendance.classlist_id == classlist.id)
        .all()
    )
    # Check if there are attendance records for the classlist
    if not attendance_records:
        return jsonify({"error": "No attendance records found for the classlist"}), 404

    # Create a dictionary to store overall status count for each student
    student_status_count = defaultdict(lambda: {"Present": 0, "Late": 0, "Absent": 0})

    for record in attendance_records:
        student = record.user
        # Increment the corresponding status count for the student
        student_status_count[student.id][record.attendance_status.value] += 1

    # Create CSV data
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    
    # Add subject and section information to the CSV header
    csv_writer.writerow(['Subject', 'Section', 'Student ID', 'First Name', 'Last Name', 'Present Count', 'Late Count', 'Absent Count'])

    for student_id, status_count in student_status_count.items():
        student = User.query.get(student_id)
        # Add subject and section information to each row
        csv_writer.writerow([classlist.subject_name, classlist.section_code,
                             student_id, student.first_name, student.last_name,
                             status_count["Present"], status_count["Late"], status_count["Absent"]])

    # Prepare response
    response = Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        content_type='text/csv',
    )
    response.headers['Content-Disposition'] = f'attachment; filename=classlist_attendance_records.csv'

    return response

@core_bp.route('/qrscanner')
@login_required
@check_is_confirmed
@admin_required
def qrscanner():
    return render_template('core/faculty/qrscanner.html')

@login_required
@check_is_confirmed
@admin_required
@core_bp.route('/get_qr', methods=['POST'])
def get_qr():
    s = request.get_json()

    # anti duplicate measure
    #last_attendance = db.session.query(Attendance).filter(Attendance.user_id==s[0]).order_by(Attendance.created.desc()).first()
    last_attendance = Attendance.query.filter(Attendance.user_id==int(s[0])).order_by(Attendance.created.desc()).first()
    if last_attendance is None:
        add_attendance(s[0], s[1])
        return ('Success!', 200)
    else:
        time_now = datetime.now()
        time_last = (time_now-last_attendance.created).total_seconds()
        # str(last_attendance.user_id) != s and 
        if time_last > 10: # ADD: change duration later
            print(f'USERID {s}, TIMENOW {time_now}, LAST TIME {last_attendance.created}, TIMELAST {time_last}')
            add_attendance(s[0], s[1])
            return ('Success!', 200)
    return ('', 204)

#################
# STUDENT VIEWS
#################

@core_bp.route('/show_qrcode')
@login_required
@check_is_confirmed
def show_qrcode():
    qr_image = generate_qr(current_user.id)
    return render_template("core/student/qrcode.html", qr_image=qr_image)

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
    base64_encoded_image = generate_qr(current_user.id)

    # Convert base64 to bytes
    qr_image_bytes = base64.b64decode(base64_encoded_image)

    # Create a BytesIO object
    image_io = io.BytesIO(qr_image_bytes)

    # Send the file for download
    return send_file(image_io, mimetype='image/png', as_attachment=True, download_name=f'{current_user.last_name}, {current_user.first_name}_qr_code.png')