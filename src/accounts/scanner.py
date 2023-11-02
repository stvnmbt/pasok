import cv2
from pyzbar.pyzbar import decode
from threading import Thread
from src import db
from src.accounts.models import Attendance, Status
from src import app

class QRCodeDetector:
    def __init__(self): 
        self._decoded = 0

    # getter method 
    @property
    def decoded(self): 
        return self._decoded

    def start(self):
        Thread(target=self.detect_qr_codes, args=(), daemon=True).start()

    def detect_qr_codes(self):
        camera_id = 0 # change based on your device
        window_name = 'OpenCV QR Code'
        qcd = cv2.QRCodeDetector()
        cap = cv2.VideoCapture(camera_id)

        with app.app_context():
            while True:
                ret, frame = cap.read()
                if ret:
                    ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
                    if ret_qr:
                        for s, p in zip(decoded_info, points):
                            if s:
                                print(s + "\n")
                                #self.decoded(s)
                                attendance = Attendance(attendance_status=Status.PRESENT, user_id=s)
                                db.session.add(attendance)
                                db.session.commit()

                                color = (0, 255, 0)
                            else:
                                color = (0, 0, 255)
                            frame = cv2.polylines(frame, [p.astype(int)], True, color, 8 )
                    cv2.imshow(window_name, frame)

                if cv2.waitKey(500) & 0xFF == ord("q"):  # Press 'q' to exit
                    break

        cv2.destroyAllWindows()

if __name__ == "__main__":
    qr_code = QRCodeDetector()
    qr_code.start()
