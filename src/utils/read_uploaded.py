import pandas as pd
from flask_login import current_user

from src import db
from src.accounts.models import ClassList, User
from src.utils.email import send_qr_email
from src.utils.generate_qr import generate_qr_path
import string
import random

from src.utils.password import generate_random_string

def generate_random_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def read_uploaded(file, school_year, semester, subject_name, section_code):
    try:
        # Read CSV file and decode it using latin1 encoding, treat the first row as headers
        data = pd.read_csv(file, encoding='latin1', header=None)

        try:
            # Check if a ClassList with the same attributes already exists
            classlist_entry = db.session.query(ClassList).filter(
                ClassList.subject_name==subject_name,
                ClassList.section_code==section_code,
                ClassList.school_year == int(school_year),
                ClassList.semester == semester,
                ClassList.faculty_creator == current_user,
            ).first()

            if not classlist_entry:
                classlist_entry = ClassList(
                    subject_name=subject_name,
                    section_code=section_code,
                    school_year=int(school_year),
                    semester=semester,
                    faculty_creator=current_user,
                )

                # Associate the classlist with the current faculty user
                classlist_entry.faculty_creator = current_user

                code = generate_random_code()
                classlist_entry.code = code  # Change this line to set the code attribute

                db.session.add(classlist_entry)

                # Commit changes to the database to get the ID for classlist_entry
                db.session.commit()
            else:
                print("ClassList with the same attributes already exists. You may want to update it or skip.")

            for index, row in data.iloc[1:].iterrows():
                # Debugging: Print row information
                print(f"Processing row {index} - {row}")

                # Skip the rows with missing or invalid values
                if pd.isnull(row[0]) or pd.isnull(row[4]) or pd.isnull(row[5]) or pd.isnull(row[6]):
                    print(f"Skipping row {index} due to missing values.")
                    continue

                # Extract student information from each row
                student_number = str(row[0]).strip()
                last_name = str(row[1]).strip()
                first_name = str(row[2]).strip()
                middle_name = str(row[3]).strip()
                email = str(row[4]).strip()

                # Check if any required field is missing
                if not all([student_number, last_name, first_name, email]):
                    print(f"Skipping row {index} due to missing values.")
                    continue  # Skip to the next iteration if there are missing values

                # Query or create the user based on the email
                existing_user = db.session.query(User).filter(User.email == email).first()

                if existing_user:
                    # Check if the association already exists before adding the user to the classlist
                    if existing_user not in classlist_entry.students:
                        # SQLAlchemy will automatically handle the association in the database
                        classlist_entry.students.append(existing_user)
                        print("User already exists. Adding the user to the classlist.")
                    else:
                        print("User is already associated with the classlist.")
                else:
                    secure_password = generate_random_string()
                    print(f"New user. Adding the user to the classlist with password: {secure_password}")

                    # Create a new user and associate with the classlist
                    user = User(
                        email=email,
                        password=secure_password,
                        first_name=first_name,
                        middle_name=middle_name,
                        last_name=last_name,
                    )

                    db.session.add(user)
                    # Associate the user with the classlist
                    # SQLAlchemy will automatically handle the association in the database
                    classlist_entry.students.append(user)

                    # db flush to get user_id
                    db.session.flush()

                    # send QR code to student email
                    user_id = (db.session.query(User).filter(User.email == email).first()).get_id()
                    subject = f'You have been enrolled to {subject_name} {section_code} classlist of PASOK attendance system'
                    body = f'Welcome! You can now use the QR code image attached to use PASOK attendance system as a student.\nUse this password to login: {secure_password}'
                    name = f'{last_name}, {first_name}'
                    send_qr_email(email, subject, body, generate_qr_path(user_id, name))
                    
            db.session.commit()
            print("Data successfully committed to the database.")

        except Exception as e:
            db.session.rollback()  # Rollback changes in case of an exception
            print(f"Error processing CSV file: {e}")
            raise ValueError("Error processing CSV file.")

    except ValueError as e:
        raise ValueError('Invalid file format. Please upload a CSV file.')

    except Exception as e:
        print(f"Error: {e}")
        raise  # Re-raise the exception for further handling

