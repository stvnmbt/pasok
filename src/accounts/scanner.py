import cv2
from pyzbar.pyzbar import decode
from threading import Thread
from src import User, db
from src.accounts.models import Attendance, Status
from src.accounts import create_app

# Create an instance of the Flask app
app = create_app()

class QRCodeDetector:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)  # Use 0 for the default camera (you can change this if you have multiple cameras)
        self.stopped = False

    @staticmethod
    def get_qr_code_from_database(user_id):
        # Connect to the database and retrieve the User object
        user = User.query.get(user_id)

        # Access the QR code attribute from the User object
        qr_code = user.qr_code

        return qr_code

    def start(self):
        Thread(target=self.detect_qr_codes, args=(), daemon=True).start()

    def detect_qr_codes(self):
        with app.app_context():
            while True:
                # Read the frame from the camera
                ret, frame = self.camera.read()

                # Decode QR codes from the frame
                decoded_objects = decode(frame)

                for obj in decoded_objects:
                    data = obj.data.decode("utf-8")

                    # Check if the QR code data is a valid user_id
                    try:
                        user_id = int(data)
                    except ValueError:
                        continue

                    # Retrieve the QR code from the database
                    qr_code = self.get_qr_code_from_database(user_id)

                    # Perform actions on the decoded QR code data
                    if qr_code is not None:
                        with app.test_request_context():
                            with app.test_client() as client:
                                with client.session_transaction() as session:
                                    session["user_id"] = user_id

                                response = client.post("/add")
                                if response.status_code == 200:
                                    print("Attendance added successfully!")

                if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to exit
                    break

        cv2.destroyAllWindows()

    def stop(self):
        self.stopped = True

if __name__ == "__main__":
    qr_code = QRCodeDetector()
    qr_code.start()
