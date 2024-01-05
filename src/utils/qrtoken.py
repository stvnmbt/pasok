import base64
import secrets

from src.accounts.models import ClassList

def generate_qrtoken(classlist_id):
    # Generate a secure random token based on classlist_id
    token_data = f"{classlist_id}{secrets.token_hex(8)}"
    # Use base64 encoding to create a URL-safe token
    token = base64.urlsafe_b64encode(token_data.encode('utf-8')).decode('utf-8')
    return token

def validate_qrtoken(token):
    try:
        # Decode the token from base64
        token_data_bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
        token_data = token_data_bytes.decode('utf-8')
        
        # Extract classlist_id from token data
        classlist_id = int(token_data[:8])

        # Check if the classlist_id exists in the database
        classlist = ClassList.query.get(classlist_id)
        if classlist:
            return True
    except Exception as e:
        # Handle decoding or validation errors
        print(f"Token validation error: {str(e)}")

    return False