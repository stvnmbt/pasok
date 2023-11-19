# src/accounts/models.py

from datetime import datetime
from flask_login import UserMixin
from src import bcrypt, db
from sqlalchemy import Enum
import enum
from src.core.views import generate_unique_user_id

class Status(enum.Enum):
    PRESENT = 'PRESENT'
    ABSENT = 'ABSENT'
    LATE = 'LATE'

class Semester(enum.Enum):
    FIRST = 'FIRST'
    SECOND = 'SECOND'
    SUMMER = 'SUMMER'

user_classlist_association = db.Table(
    'user_classlist_association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('classlist_id', db.Integer, db.ForeignKey('classlist.id'))
)

class ClassList(db.Model):
    __tablename__ = "classlist"

    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    school_year = db.Column(db.Integer, nullable=False)
    semester = db.Column(Enum(Semester, values_callable=lambda x: [str(e.value) for e in Semester]), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    
    students = db.relationship('User', secondary=user_classlist_association, back_populates='classlists')

    user_classlist = db.relationship('User', back_populates='created_classlists')
    faculty_creator = db.relationship('User', back_populates='created_classlists')

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    attendance_status = db.Column(Enum(Status, values_callable=lambda x: [str(e.value) for e in Status]), nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_attendance = db.relationship('User', back_populates='classlist_attendance')
    

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(256), unique=True, nullable=False)
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
    section_name = db.Column(db.String(20))
    present_count = db.Column(db.Integer, nullable=True)
    late_count = db.Column(db.Integer, nullable=True)
    absent_count = db.Column(db.Integer, nullable=True)

    # Add this line to initialize the relationships
    classlists = db.relationship('ClassList', secondary='user_classlist_association', back_populates='students')
    classlist_attendance = db.relationship('Attendance', back_populates='user_attendance')
    created_classlists = db.relationship('ClassList', back_populates='faculty_creator')

    def __init__(
        self, email, password, first_name, middle_name, last_name, section_name='', present_count=0, late_count=0, absent_count=0, qr_code=None, is_confirmed=False, confirmed_on=None, is_faculty=False
    ):    
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.created_on = datetime.now()
        self.is_faculty = is_faculty
        self.is_confirmed = is_confirmed
        self.confirmed_on = confirmed_on
        self.qr_code = qr_code
        self.section_name = section_name
        self.present_count = present_count
        self.late_count = late_count
        self.absent_count = absent_count
        self.user_id = generate_unique_user_id(email, first_name, last_name)
    def __repr__(self):
        return f"<email {self.email}>"
