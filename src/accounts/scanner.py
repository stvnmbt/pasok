import cv2
from pyzbar.pyzbar import decode
from threading import Thread
from flask import Flask, render_template, redirect
from src import User
from src.accounts.models import Attendance, Status
from src.accounts import create_app
import requests

# Create an instance of the Flask app
app = create_app()

class QRCodeDetector:
    def __init__(self):
        self.camera = cv2.VideoCapture(1)  # Use 0 for the default camera (you can change this if you have multiple cameras)
        self.stopped = False

    # Rest of your QRCodeDetector class

    @staticmethod
    def extract_user_info_from_qr_code(qr_code_content):
        user_id = qr_code_content[:3]
        first_name = qr_code_content[3:6]
        last_name = qr_code_content[6:]

        return user_id, first_name, last_name

    def start(self):
        Thread(target=self.detect_qr_codes, args=(), daemon=True).start()

    def detect_qr_codes(self):
        with app.app_context():
            while True:
                # Read the frame from the camera
                _, frame = self.camera.read()

                # Decode QR codes from the frame
                decoded_objects = decode(frame)

                # Draw rectangles around the detected QR codes
                for obj in decoded_objects:
                    # Extract the QR code coordinates
                    x, y, w, h = obj.rect

                    # Draw a rectangle around the QR code
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Decode the QR code data
                    data = obj.data.decode("utf-8")

                    # Process the decoded QR code data
                    self.process_decoded_qr_code(data)

                # Display the frame with the detected QR codes
                cv2.imshow("QR Code Detection", frame)

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
        user_id, first_name, last_name = self.extract_user_info_from_qr_code(qr_code_content)

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
