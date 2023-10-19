from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from src import db
from src.utils.decorators import check_is_confirmed
from src.accounts.models import Attendance, Status

core_bp = Blueprint("core", __name__)

@core_bp.route("/")
@login_required
@check_is_confirmed
def home():
    attendance_records = Attendance.query.order_by(Attendance.created.desc())
    return render_template("core/index.html", attendance_records=attendance_records)



@core_bp.route("/add", methods=["GET", "POST"])
@login_required
@check_is_confirmed
def add():
    if request.method == "POST":
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
    return render_template("core/index.html", attendance_records=attendance_records)

