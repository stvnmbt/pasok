from flask import flash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import base64
import secrets
from datetime import datetime, timedelta
from src.accounts.models import ClassList
from src.utils.scanner import add_attendance

SECRET_KEY = "your_secret_key"
SECURITY_PASSWORD_SALT = "your_security_salt"

def generate_qrtoken(classlist_id):
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    token_data = f"{secrets.token_urlsafe(16)}:{int(classlist_id):08d}:{timestamp}"
    token = base64.urlsafe_b64encode(token_data.encode('utf-8')).decode('utf-8')
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    token_with_expiration = serializer.dumps(token, salt=SECURITY_PASSWORD_SALT)

    return token_with_expiration

def validate_qrtoken(token, lateness_threshold_minutes, userid, classlistid):
    try:
        serializer = URLSafeTimedSerializer(SECRET_KEY)
        token = serializer.loads(token, salt=SECURITY_PASSWORD_SALT, max_age=1)

        # Decode the token from base64
        token_data_bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
        token_data = token_data_bytes.decode('utf-8')

        # Split token data into random_string, classlist_id, and timestamp
        random_string, classlist_id_str, timestamp_str = token_data.split(':', 2)
        
        # Convert classlist_id to integer
        classlist_id = int(classlist_id_str)

        # Parse the timestamp
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')

        # Check if the student is late based on the threshold
        current_time = datetime.utcnow()
        lateness_delta = current_time - timestamp
        print(f"{current_time} -- {lateness_delta} vs {timestamp}")
        if lateness_delta > timedelta(minutes=lateness_threshold_minutes):
            add_attendance(userid, True, classlistid)
            flash('Attendance recorded successfully (Late).', 'warning')
            return True
        else:
            add_attendance(userid, False, classlistid)
            flash('Attendance recorded successfully.', 'success')

        classlist = ClassList.query.get(classlist_id)
        if classlist:
            return True
    except SignatureExpired:
        print("Token has expired.")
    except BadSignature:
        print("Invalid token signature.")
    except ValueError as ve:
        print(f"Error extracting classlist_id: {str(ve)}")

    return False
