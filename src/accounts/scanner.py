import cv2
from pyzbar.pyzbar import decode
from threading import Thread
from flask import Flask, render_template, redirect, request
from src import User
from src.accounts.models import Attendance, Status
from src.accounts import create_app
import requests

# Create an instance of the Flask app
app = create_app()

class QRCodeDetector:

    def start(self):
        Thread(target=self.detect_qr_codes, args=(), daemon=True).start()

    def detect_qr_codes(self):
        camera_id = 1
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
                                #print(s)
                                # Decode the QR code data
                                #data = obj.data.decode("utf-8")

                                # Process the decoded QR code data
                                client = app.test_client()
                                client.get('/core/add', headers=list(request.headers))

                                color = (0, 255, 0)
                            else:
                                color = (0, 0, 255)
                            frame = cv2.polylines(frame, [p.astype(int)], True, color, 8 )
                    cv2.imshow(window_name, frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to exit
                    break

        cv2.destroyAllWindows()

    def process_decoded_qr_code(self, data):
        # Check if the QR code data is a valid user_id
        try:
            user_id = int(data)
        except ValueError:
            return

        # Extract user information from the QR code content
        qr_code_content = data

        # Retrieve the User object
        user = User.query.get(user_id)

        # Perform actions on the decoded QR code data
        if user is not None:
            # Make a POST request to the /add route within the 'core' blueprint of the Flask application
            with app.test_request_context():
                with app.test_client() as client:
                    response = client.post("/core/add", data={"user_id": user_id}, follow_redirects=True, method="post")
                    if response.status_code == 200:
                        print("Attendance added successfully!")

        self.stopped = True

if __name__ == "__main__":
    qr_code = QRCodeDetector()
    qr_code.start()
