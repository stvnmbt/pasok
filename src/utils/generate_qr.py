import base64
import tempfile
import qrcode
import requests
from qrcode.image.styledpil import StyledPilImage

def temp_icon():
    image_url = "https://storage.googleapis.com/pasoksystem.appspot.com/static/images/PUP%20logo%20white%20bg.png"
    response = requests.get(image_url)

    # Create a temporary file to store the image
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_file.write(response.content)
    
    return temp_file.name

def generate_qr(user_id):
    # Generate the QR code
    qr = qrcode.QRCode(
        version=5,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(user_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as qr_temp_file:
        # Create the QR code image with the embedded image
        qr_code_image = qr.make_image(image_factory=StyledPilImage, embeded_image_path=temp_icon())

        # Save the QR code image to the temporary file
        qr_code_image.save(qr_temp_file, format='PNG')

        # Open the saved QR code image
        with open(qr_temp_file.name, 'rb') as qr_temp_file:
            # Encode the image to base64
            base64_encoded_image = base64.b64encode(qr_temp_file.read()).decode()

            # Optionally, return the base64-encoded image
            return base64_encoded_image
        
def generate_qr_path(user_id, name):
    qr = qrcode.QRCode(
        version=5,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(user_id)

    with tempfile.NamedTemporaryFile(delete=False, prefix=name, suffix=".png") as qr_temp_file:
        # Create the QR code image with the embedded image
        qr_code_image = qr.make_image(image_factory=StyledPilImage, embeded_image_path=temp_icon())

        # Save the QR code image to the temporary file
        qr_code_image.save(qr_temp_file, format='PNG')
    
    return qr_temp_file.name