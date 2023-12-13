from src import db
from src.accounts.models import Attendance

def count_attendance(status, user_id, classlist_ids):
    count = db.session.query(Attendance).filter(
        Attendance.user_id == user_id,
        Attendance.attendance_status == status,
        Attendance.classlist_id.in_(classlist_ids)
    ).count()
    return count