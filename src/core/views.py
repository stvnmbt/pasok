from flask import Blueprint, render_template, redirect, url_for, request
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
def add(page=1):
    per_page = 15

    if request.method == "POST":
        attendance = Attendance(attendance_status=Status.PRESENT, user_id=current_user.id)
        db.session.add(attendance)
        db.session.commit()

    attendance_records = Attendance.query.order_by(Attendance.created.desc())
    
    return render_template("core/index.html", attendance_records=attendance_records)
