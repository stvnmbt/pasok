from sqlalchemy import delete
from src import db
from src.accounts.models import Attendance, Status, User

def add_attendance(s, isLate):
    user = User.query.get(s)
    status = Status.PRESENT
    if isLate:
        status = Status.LATE

    attendance = Attendance(attendance_status=status, user_id=s) # ADD: Change status with variable

    if attendance.attendance_status==Status.PRESENT:
        user.present_count += 1
    elif attendance.attendance_status==Status.LATE:
        user.late_count += 1
    elif attendance.attendance_status==Status.ABSENT:
        user.absent_count += 1

    db.session.add(attendance)
    db.session.commit()

def mark_absent():
    users = db.session.query(Attendance)