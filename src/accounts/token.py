from itsdangerous import URLSafeTimedSerializer
from src import app
import os

def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=os.environ["SECURITY_PASSWORD_SALT"])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=os.environ["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
        return email
    except Exception:
        return False