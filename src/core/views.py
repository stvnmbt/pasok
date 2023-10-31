from flask import Blueprint, render_template
from flask_login import login_required, current_user

from src import db
from src.utils.decorators import check_is_confirmed
from src.accounts.models import Attendance, Status

core_bp = Blueprint("core", __name__)


@core_bp.route("/")
@login_required
@check_is_confirmed
def home_faculty():
    return render_template("core/faculty/index.html")

@core_bp.route("/")
@login_required
@check_is_confirmed
def home_student():
    return render_template("core/student/index.html")

@core_bp.route("/add", methods=["GET", "POST"])
@login_required
@check_is_confirmed
def add():
    attendance = Attendance(attendance_status=Status.PRESENT, user_id=current_user.id)
    db.session.add(attendance)
    db.session.commit()
    attendance_records = Attendance.query.order_by(Attendance.created.desc())
    return render_template("core/faculty/index.html", attendance_records=attendance_records)

@core_bp.route('/faculty/records')
def records():
    return render_template('core/faculty/records.html')

@core_bp.route('/faculty/classlist')
def classlist():
    return render_template('core/faculty/classlist.html')
