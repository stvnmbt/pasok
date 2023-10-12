import cv2
from pyzbar.pyzbar import decode
from threading import Thread
from src import User, db, Attendance 
from flask import Flask

class QRCodeDetector:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)  # Use 0 for the default camera (you can change this if you have multiple cameras)
        self.stopped = False

    def start(self):
        Thread(target=self.detect_qr_codes, args=(), daemon=True).start()

    def detect_qr_codes(self):
        while not self.stopped:
            ret, frame = self.camera.read()  # Capture a frame
            decoded_objects = decode(frame)

            for obj in decoded_objects:
                data = obj.data.decode("utf-8")
                # Perform actions based on the decoded QR code data
                user = User.query.filter_by(qr_code=data).first()
                if user:
                    # Mark the user as present for attendance
                    attendance = Attendance(attendance_status='PRESENT', user_id=user.id)
                    db.session.add(attendance)
                    db.session.commit()

    def stop(self):
        self.stopped = True
        self.camera.release()

# Create an instance of the QRCodeDetector
qr_code_detector = QRCodeDetector()

# Start the background thread for QR code detection
qr_code_detector.start()

# To stop the QR code detection thread, call qr_code_detector.stop()
# qr_code_detector.stop()
