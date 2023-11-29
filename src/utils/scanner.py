from src import db
from src.accounts.models import Attendance, Status, User, assoc

def add_attendance(id, isLate: bool):
    user = User.query.get(id)
    status = Status.PRESENT
    if isLate:
        status = Status.LATE

    classlist_id = db.session.query(assoc.c.classlist_id).filter(assoc.c.user_id == id).first()[0]

    attendance = Attendance(attendance_status=status, user_id=id, classlist_id=classlist_id)

    if attendance.attendance_status==Status.PRESENT:
        user.present_count += 1
    elif attendance.attendance_status==Status.LATE:
        user.late_count += 1

    db.session.add(attendance)
    db.session.commit()

def add_absent(id, classlist_id, status: Status):
    user = User.query.get(id)
    
    attendance = Attendance(attendance_status=status, user_id=id, classlist_id=classlist_id)
    user.absent_count += 1
    
    db.session.add(attendance)
    db.session.commit()