import cv2
from src import db
from src.accounts.models import Attendance, Status, User
from datetime import datetime

def add_attendance(s):
    user = User.query.get(s)
    attendance = Attendance(attendance_status=Status.PRESENT, user_id=s)
    db.session.add(attendance)
    # ADD: TRIGGER GOOD BUZZER

    if attendance.attendance_status==Status.PRESENT:
        user.present_count += 1
    elif attendance.attendance_status==Status.LATE:
        user.late_count += 1
    elif attendance.attendance_status==Status.ABSENT:
        user.absent_count += 1

    db.session.commit()

def detect_qr_codes():
    camera_id = 1 # set to 1 to access device's second camera
    qcd = cv2.QRCodeDetector()
    cap = cv2.VideoCapture(camera_id)

    while True:
        ret, frame = cap.read()
        if ret:
            ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
            if ret_qr:
                for s, p in zip(decoded_info, points):
                    if s:
                        last_attendance = Attendance.query.order_by(Attendance.created.desc()).first()
                        
                        # anti duplicate measure
                        if last_attendance is None:
                            add_attendance(s)
                        else:
                            time_now = datetime.utcnow()
                            time_last = (time_now-last_attendance.created).total_seconds()

                            if (str(last_attendance.user_id) != s) or (time_last > 300):
                                add_attendance(s)

                        color = (0, 255, 0)
                    else:
                        color = (0, 0, 255)
                    frame = cv2.polylines(frame, [p.astype(int)], True, color, 8 )

def gen_frames():  
    while True:
        success, frame = cv2.VideoCapture(1).read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')