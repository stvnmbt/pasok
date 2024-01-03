def is_password_complex(password):
    # Add your password complexity requirements here
    return (
        len(password) >= 8 and
        any(c.islower() for c in password) and
        any(c.isupper() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in "!@#$%^&*()-_=+{};:,<.>/?'" for c in password)
    )