from datetime import datetime
from flask_login import UserMixin
from src import bcrypt, db
from sqlalchemy import Enum, func
import enum
from sqlalchemy.orm import relationship

class Status(enum.Enum):
    PRESENT = 'PRESENT'
    ABSENT = 'ABSENT'
    LATE = 'LATE'

class Semester(enum.Enum):
    FIRST = 'FIRST'
    SECOND = 'SECOND'
    SUMMER = 'SUMMER'

class ClassList(db.Model):
    __tablename__ = "classlist"

    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(20), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    school_year = db.Column(db.Integer, nullable=False)
    semester = db.Column(Enum(Semester, values_callable=lambda x: [str(e.value) for e in Semester]), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_classlist = db.relationship('User', foreign_keys=user_id, backref='user_classlist')

class Subject(db.Model):  # Define Subject model first
    __tablename__ = "subject"

    id = db.Column(db.Integer, primary_key=True)
    # Add other columns as needed

    # Define a relationship with the Attendance model
    attendance = db.relationship('Attendance', back_populates='subject')

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    attendance_status = db.Column(Enum(Status), nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=True)
    user = db.relationship('User', back_populates='attendance')
    subject = db.relationship('Subject', back_populates='attendance')
    section = db.relationship('Section', back_populates='attendance')  # Add this line
    

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    middle_name = db.Column(db.String(150), nullable=True)
    last_name = db.Column(db.String(150), nullable=False)
    qr_code = db.Column(db.LargeBinary, nullable=True)
    is_faculty = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    created_on = db.Column(db.DateTime, nullable=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    section_code = db.Column(db.String(20))
    present_count = db.Column(db.Integer, nullable=True)
    late_count = db.Column(db.Integer, nullable=True)
    absent_count = db.Column(db.Integer, nullable=True)

    classlist_id = db.Column(db.Integer, db.ForeignKey('classlist.id'))
    classlist = db.relationship('ClassList', foreign_keys=classlist_id)

    # Add the following relationship
    attendance = db.relationship('Attendance', back_populates='user')


    def __init__(
        self, email, password, first_name, middle_name, last_name, section_code='', present_count=0, late_count=0, absent_count=0, qr_code=None, is_confirmed=False, confirmed_on=None, is_faculty=False
    ):  
        self.email = email
        self.password = bcrypt.generate_password_hash(password)
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.created_on = datetime.now()
        self.is_faculty = is_faculty
        self.is_confirmed = is_confirmed
        self.confirmed_on = confirmed_on
        self.qr_code = qr_code
        self.section_code = section_code
        self.present_count = present_count
        self.late_count = late_count
        self.absent_count = absent_count
        
    def __repr__(self):
        return f"<email {self.email}>"


class Section(db.Model):
    __tablename__ = "section"

    id = db.Column(db.Integer, primary_key=True)
    # Add other columns as needed

    # Define a relationship with the Attendance model
    attendance = db.relationship('Attendance', back_populates='section')

