import base64
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, send_file, jsonify, Response, redirect, flash, current_app, url_for
import io
from flask_login import login_required, current_user
from src import db
from src.utils.decorators import admin_required, admin_required, check_is_confirmed
from src.accounts.models import Attendance, Status, User, ClassList, assoc
import io
import os
import csv
from src.utils.generate_qr import generate_qr
from src.utils.scanner import add_attendance
import json
import pandas as pd
import random
import string
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash

bcrypt = Bcrypt()
core_bp = Blueprint("core", __name__)

@core_bp.route("/")
@login_required
@check_is_confirmed
def home():
    user = current_user
    if user.is_faculty:
        classlists = ClassList.query.all()
        return render_template("core/faculty/index.html", classlists=classlists)
    else:
        return render_template("core/student/index.html")


@core_bp.route('/account_settings', methods=['GET', 'POST'])
@login_required
@check_is_confirmed
def account_settings():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if the current password is correct
        if not check_password_hash(current_user.password, current_password):
            flash('Incorrect current password', 'danger')
        elif new_password != confirm_password:
            flash('New password and confirm password do not match', 'danger')
        elif not is_password_complex(new_password):
            flash('Password does not meet complexity requirements', 'danger')
        else:
            # Update the user's password
            current_user.password = generate_password_hash(new_password).decode('utf-8')

            # Check if new names are provided
            new_first_name = request.form.get('new_first_name')
            new_middle_name = request.form.get('new_middle_name')
            new_last_name = request.form.get('new_last_name')

            if new_first_name:
                current_user.first_name = new_first_name
            if new_middle_name:
                current_user.middle_name = new_middle_name
            if new_last_name:
                current_user.last_name = new_last_name

            db.session.commit()
            flash('Account updated successfully', 'success')
            return redirect(url_for('core.home'))

    return render_template('core/account_settings.html', user=current_user)


def is_password_complex(password):
    # Add your password complexity requirements here
    return (
        len(password) >= 8 and
        any(c.islower() for c in password) and
        any(c.isupper() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in "!@#$%^&*()-_=+{};:,<.>/?'" for c in password)
    )

#################
# FACULTY VIEWS
#################

@core_bp.route("/get_attendance_data")
@login_required
@check_is_confirmed
@admin_required
def get_attendance_data():
    # Query the database to get the attendance data
    attendance_data = db.session.query(
        db.func.sum(User.present_count).label('present_count'),
        db.func.sum(User.late_count).label('late_count'),
        db.func.sum(User.absent_count).label('absent_count')
    ).first()

    # Map the data to a format suitable for the frontend
    result = [
        {'status': 'Present', 'count': attendance_data.present_count, 'color': 'green'},
        {'status': 'Late', 'count': attendance_data.late_count, 'color': 'orange'},
        {'status': 'Absent', 'count': attendance_data.absent_count, 'color': 'red'},
    ]

    return jsonify(result)

@core_bp.route("/realtime")
@login_required
@check_is_confirmed
@admin_required
def realtime():
    attendance_user = db.session.query(Attendance, User)\
    .join(User, User.id == Attendance.user_id)\
    .join(ClassList, Attendance.classlist_id == ClassList.id)\
    .add_columns(User.first_name, User.last_name, ClassList.section_code, Attendance.created, Attendance.attendance_status)\
    .order_by(Attendance.created.desc())\
    .all()

    return render_template("core/faculty/realtime.html", attendance_user=attendance_user, zip=zip)

@core_bp.route('/records')
@login_required
@check_is_confirmed
@admin_required
def records():
    students = db.session.query(User, assoc)\
    .join(User, User.id == assoc.c.user_id)\
    .join(ClassList, ClassList.id == assoc.c.classlist_id)\
    .add_columns(User.first_name, User.last_name, User.middle_name, ClassList.section_code, User.present_count, User.late_count, User.absent_count)\
    .filter(User.is_faculty == False)\
    .order_by(User.last_name.asc())\
    .all()
    #students = db.session.query(User).filter(User.is_faculty == False).all()

    return render_template('core/faculty/records.html', students=students)

@core_bp.route('/display_classlist/<int:classlist_id>', methods=['GET'])
@login_required
@check_is_confirmed
@admin_required
def display_classlist(classlist_id):
    # Fetch detailed information for the specified classlist_id
    classlist_entry = ClassList.query.get_or_404(classlist_id)
    users = classlist_entry.students

    # Render the template with detailed information
    return render_template('core/faculty/classlist_details.html', classlist_entry=classlist_entry, users=users)

@core_bp.route('/delete_classlist/<int:classlist_id>', methods=['GET', 'POST'])
@login_required
@check_is_confirmed
@admin_required
def delete_classlist(classlist_id):
    try:
        # Fetch the class list entry from the database
        classlist_entry = ClassList.query.get(classlist_id)

        if classlist_entry:
            # Manually remove students from the classlist
            for student in classlist_entry.students:
                print(f"Removing student {student.id} from classlist {classlist_entry.id}")

                # Manually delete association from user_classlist_association table
                db.session.execute(assoc.delete().where(
                    (assoc.c.user_id == student.id) & (assoc.c.classlist_id == classlist_entry.id)
                ))

            # Commit the changes to the association table
            db.session.commit()

            # Remove the class list from the students' classlists
            classlist_entry.students = []

            # Delete the class list entry
            db.session.delete(classlist_entry)

            # Commit the changes to the database
            db.session.commit()

            flash('Class list deleted successfully', 'success')
        else:
            flash('Class list not found', 'error')

    except Exception as e:
        db.session.rollback()
        flash('Error deleting class list', 'error')
        current_app.logger.error(f"Error deleting class list: {str(e)}")

    # Redirect back to the class list collection
    return redirect(url_for('core.classlist'))

@core_bp.route('/classlist', methods=['GET'])
@login_required
@check_is_confirmed
@admin_required
def classlist():
    # Fetch data and prepare it to be passed to the template
    classlist_entries = ClassList.query.filter_by(faculty_creator=current_user).all()
    classlistId = classlist_entries[0].id if classlist_entries else None

    # Fetch a list of class lists created by the current faculty user
    classlist_data = ClassList.query.filter_by(faculty_creator=current_user).all()

    # Manually convert to JSON format, handle None case
    classlistId_json = json.dumps(classlistId) if classlistId is not None else None

    # Example of creating classlists_by_user dynamically
    classlists_by_user = {current_user.id: [entry.subject_name for entry in classlist_entries]}

    return render_template('core/faculty/classlist.html', classlistId_json=classlistId_json, classlists_by_user=classlists_by_user, classlist_data=classlist_data)

@core_bp.route("/export_attendance_csv", methods=["GET"])
@login_required
@check_is_confirmed
@admin_required
def export_classlist_attendance_csv():
    classlist_id = request.args.get('classlist_id')

    classlist = ClassList.query.get(classlist_id)

    # Check if the user has permission to access this classlist
    if current_user.is_faculty and current_user != classlist.user_classlist:
        return jsonify({"error": "You don't have permission to access this classlist"}), 403

    # Get the students associated with the classlist
    students = classlist.students.all()

    # Create CSV data
    csv_data = io.StringIO()
    csv_writer = csv.writer(csv_data)

    # Add subject and section information to the CSV header
    csv_writer.writerow(['Subject:', classlist.subject_name])
    csv_writer.writerow(['Section:', classlist.section_code])
    csv_writer.writerow([])  # Add an empty row for better readability
    csv_writer.writerow(['Last Name', 'First Name', 'Middle Name', 'Present', 'Late', 'Absent'])

    for student in students:
        # Add student data to each row
        csv_writer.writerow([student.last_name, student.first_name, student.middle_name,
                             student.present_count, student.late_count, student.absent_count])

    # Prepare response
    response = Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        content_type='text/csv',
    )
    response.headers['Content-Disposition'] = f'attachment; filename=classlist_attendance_records.csv'

    return response

def generate_random_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(8))
    return password

def read_and_store_data(file, school_year, semester):
    try:
        # Read CSV file and decode it using latin1 encoding, treat the first row as headers
        data = pd.read_csv(file, encoding='latin1', header=None)

        subject_name = str(data.iloc[0, 1]).strip()
        section_code = str(data.iloc[0, 5]).strip()
        print(f"Subject Name: {subject_name}, Section Name: {section_code}")

        try:
            # Check if any required field is missing
            if not all([subject_name, section_code]):
                raise ValueError("Missing values in subject or section information.")

            # Check if a ClassList with the same attributes already exists
            classlist_entry = ClassList.query.filter_by(
                subject_name=subject_name,
                section_code=section_code,
                school_year=school_year,
                semester=semester,
                faculty_creator=current_user,
            ).first()

            if not classlist_entry:
                classlist_entry = ClassList(
                    subject_name=subject_name,
                    section_code=section_code,
                    school_year=school_year,
                    semester=semester,
                    faculty_creator=current_user,
                )

                # Associate the classlist with the current faculty user
                classlist_entry.faculty_creator = current_user

                db.session.add(classlist_entry)

                # Commit changes to the database to get the ID for classlist_entry
                db.session.commit()
            else:
                # If a ClassList with the same attributes already exists, you can choose to update it or skip
                print("ClassList with the same attributes already exists. You may want to update it or skip.")

            for index, row in data.iloc[3:].iterrows():
                # Debugging: Print row information
                print(f"Processing row {index} - {row}")

                # Skip the rows with missing or invalid values
                if pd.isnull(row[0]) or pd.isnull(row[4]) or pd.isnull(row[5]) or pd.isnull(row[6]):
                    print(f"Skipping row {index} due to missing values.")
                    continue

                # Extract student information from each row
                student_number = str(row[0]).strip()
                last_name = str(row[1]).strip()
                first_name = str(row[2]).strip()
                middle_name = str(row[3]).strip()
                email = str(row[4]).strip()
                mobile_number = str(row[5]).strip()
                delivery_mode = str(row[6]).strip()
                remarks = str(row[7]).strip()

                # Check if any required field is missing
                if not all([student_number, last_name, first_name, email]):
                    print(f"Skipping row {index} due to missing values.")
                    continue  # Skip to the next iteration if there are missing values

                # Query or create the user based on the email
                existing_user = User.query.filter_by(email=email).first()

                if existing_user:
                    # Check if the association already exists before adding the user to the classlist
                    if existing_user not in classlist_entry.students:
                        # SQLAlchemy will automatically handle the association in the database
                        classlist_entry.students.append(existing_user)
                        print("User already exists. Adding the user to the classlist.")
                    else:
                        print("User is already associated with the classlist.")
                else:
                    # Create a new user and associate with the classlist
                    user = User(
                        email=email,
                        password=generate_random_password(),
                        first_name=first_name,
                        middle_name=middle_name,
                        last_name=last_name,
                    )

                    db.session.add(user)
                    # Associate the user with the classlist
                    # SQLAlchemy will automatically handle the association in the database
                    classlist_entry.students.append(user)
                    print(f"New user. Adding the user to the classlist with password: {user.password}")

            # Commit changes to the database after processing all rows
            db.session.commit()

            print("Data successfully committed to the database.")

        except Exception as e:
            db.session.rollback()  # Rollback changes in case of an exception
            print(f"Error processing CSV file: {e}")
            raise ValueError("Error processing CSV file.")

    except ValueError as e:
        raise ValueError('Invalid file format. Please upload a CSV file.')

    except Exception as e:
        print(f"Error: {e}")
        raise  # Re-raise the exception for further handling


@core_bp.route('/upload_classlist', methods=['POST'])
@login_required
@check_is_confirmed
@admin_required
def upload_classlist():
    try:
        school_year = request.form.get('school_year')
        semester = request.form.get('semester')

        # Assuming 'files[]' is the name attribute of your file input in the form
        uploaded_files = request.files.getlist('files[]')

        for file in uploaded_files:
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            try:
                # Call your function here without saving to the local file system
                read_and_store_data(file, school_year, semester)
                flash('Data successfully saved to the database.')
            except ValueError as e:
                flash(f'Error processing file: {str(e)}')

        return redirect(request.url)

    except Exception as e:
        # Handle other exceptions or errors
        flash(f"Error: {e}")
        return redirect(request.url)

@core_bp.route('/display_data', methods=['GET'])
@login_required
@check_is_confirmed
@admin_required
def display_data():
    # Query all data from the ClassList table
    classlist_data = ClassList.query.filter_by(creator_id=current_user.id).all()
    
    # Print the number of ClassList entries retrieved
    print(f"Number of ClassList entries: {len(classlist_data)}")

    # Create a list to store dictionaries with classlist and user information
    classlist_with_users = []

    # Iterate through each ClassList object and find the corresponding User objects
    for classlist_entry in classlist_data:
        users = classlist_entry.students  # Use the relationship attribute
        users_info = [{'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email} for user in users]

        # Append a dictionary with classlist and user information to the list
        classlist_with_users.append({
            'classlist_entry': {'subject_name': classlist_entry.subject_name, 'section_code': classlist_entry.section_code},
            'users': users_info
        })

    # Debugging print statements (move this outside the loop)
    for item in classlist_with_users:
        print(f"Classlist Entry: {item['classlist_entry']['subject_name']} - {item['classlist_entry']['section_code']}")
        print(f"Number of Users: {len(item['users'])}")

    for item in classlist_with_users:
        for user in item['users']:
            print(f"User: {user['first_name']} {user['last_name']} ({user['email']})")

    # Render the template
    return render_template('display_data.html', classlist_with_users=classlist_with_users)

@core_bp.route('/qrscanner')
@login_required
@check_is_confirmed
@admin_required
def qrscanner():
    classlists = db.session.query(ClassList).all()
    return render_template('core/faculty/qrscanner.html', classlists=classlists)

@core_bp.route('/send_absents', methods=['POST'])
@login_required
@check_is_confirmed
@admin_required
def send_absents():
    classlist_id = request.form['classlistId']

    # if a user's last attendance is more than an hour ago, or if it does not exist, add to absents list
    threshold_time = datetime.now() - timedelta(hours=1)
    
    absents = (
        db.session.query(User)
        .join(assoc)
        .join(ClassList)
        .outerjoin(User.classlist_attendance)
        .group_by(User.id)
        .having(
            (db.func.max(Attendance.created) < threshold_time) |
            (db.func.count(Attendance.id) == 0)
        )
        .filter(ClassList.id == classlist_id)
        .all()
    )

    for absent in absents:
        add_attendance(absent.id, classlist_id, Status.ABSENT)

    # Return a response if necessary
    return 'Success'

@core_bp.route('/get_qr', methods=['POST'])
@login_required
@check_is_confirmed
@admin_required
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