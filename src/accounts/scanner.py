import cv2
from pyzbar.pyzbar import decode
from threading import Thread
from src import db
from src.accounts.models import Attendance, Status, User
from src import app
from datetime import datetime, timezone

class QRCodeDetector:
    def start(self):
        Thread(target=self.detect_qr_codes, args=(), daemon=True).start()

    def detect_qr_codes(self):
        camera_id = 0 # set to 1 to access device's second camera
        window_name = 'OpenCV QR Code'
        qcd = cv2.QRCodeDetector()
        cap = cv2.VideoCapture(camera_id)
        delay = 500 # how often the camera scans for qr code in miliseconds

        with app.app_context():
            while True:
                ret, frame = cap.read()
                if ret:
                    ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
                    if ret_qr:
                        for s, p in zip(decoded_info, points):
                            if s:
                                user = User.query.get(s)

                                last_attendance = Attendance.query.order_by(Attendance.created.desc()).first()
                                time_now = datetime.utcnow()
                                time_last = (time_now-last_attendance.created).total_seconds()
                                print(last_attendance, last_attendance.id, last_attendance.user_id, s, time_now, last_attendance.created, time_last)
                                if (last_attendance is None) or (str(last_attendance.user_id) != s) or (time_last > 300) : # anti duplicate measure
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
                                # ADD: else TRIGGER BAD BUZZER

                                color = (0, 255, 0)
                            else:
                                color = (0, 0, 255)
                            frame = cv2.polylines(frame, [p.astype(int)], True, color, 8 )
                    cv2.imshow(window_name, frame)

                if cv2.waitKey(delay) & 0xFF == ord("q"):  # Press 'q' to exit
                    break

        cv2.destroyAllWindows()

if __name__ == "__main__":
    qr_code = QRCodeDetector()
    qr_code.start()
