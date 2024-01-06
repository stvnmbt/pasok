import random
import string

def is_password_complex(password):
    # Add your password complexity requirements here
    return (
        len(password) >= 8 and
        any(c.islower() for c in password) and
        any(c.isupper() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in "!@#$%^&*()-_=+{};:,<.>/?'" for c in password)
    )

def generate_random_string():
    # Define character sets for lowercase letters, uppercase letters, digits, and special characters
    lowercase_letters = string.ascii_lowercase
    uppercase_letters = string.ascii_uppercase
    digits = string.digits
    special_characters = string.punctuation

    # Ensure at least one character from each category
    random_lowercase = random.choice(lowercase_letters)
    random_uppercase = random.choice(uppercase_letters)
    random_digit = random.choice(digits)
    random_special = random.choice(special_characters)

    # Generate the remaining characters randomly
    remaining_length = 6  # 10 - 4 (one from each category)
    random_chars = ''.join(random.choices(string.ascii_letters + digits + special_characters, k=remaining_length))

    # Combine all the characters and shuffle them
    generated_string = ''.join([random_lowercase, random_uppercase, random_digit, random_special, random_chars])
    shuffled_string = ''.join(random.sample(generated_string, len(generated_string)))

    return shuffled_string