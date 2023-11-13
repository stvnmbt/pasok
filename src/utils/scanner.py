from sqlalchemy import delete
from src import db
from src.accounts.models import Attendance, Status, User

def add_attendance(s):
    user = User.query.get(s)
    attendance = Attendance(attendance_status=Status.LATE, user_id=s) # ADD: Change status with variable

    if attendance.attendance_status==Status.PRESENT:
        user.present_count += 1
    elif attendance.attendance_status==Status.LATE:
        user.late_count += 1
    elif attendance.attendance_status==Status.ABSENT:
        user.absent_count += 1

    db.session.add(attendance)
    db.session.commit()