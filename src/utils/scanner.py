from sqlalchemy import delete
from src import db
from src.accounts.models import Attendance, Status, User, assoc

def add_attendance(s, isLate):
    user = User.query.get(s)
    status = Status.PRESENT
    if isLate:
        status = Status.LATE

    classlist_id = db.session.query(assoc.c.classlist_id).filter(assoc.c.user_id == s).first()[0]

    attendance = Attendance(attendance_status=status, user_id=s, classlist_id=classlist_id)

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