from datetime import datetime
from flask_login import UserMixin
from src import bcrypt, db
from sqlalchemy import Enum
import enum

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

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    attendance_status = db.Column(Enum(Status, values_callable=lambda x: [str(e.value) for e in Status]), nullable=False)
    created = db.Column(db.DateTime, default=datetime.now, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_attendance = db.relationship('User', foreign_keys=user_id, backref='user_attendance')

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    middle_name = db.Column(db.String(150), nullable=True)
    last_name = db.Column(db.String(150), nullable=False)
    is_faculty = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    created_on = db.Column(db.DateTime, nullable=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    section_code = db.Column(db.String(20))
    present_count = db.Column(db.Integer, nullable=True)
    late_count = db.Column(db.Integer, nullable=True)
    absent_count = db.Column(db.Integer, nullable=True)

    classlist_id = db.Column(db.Integer, db.ForeignKey('classlist.id'))
    classlist = db.relationship('ClassList', foreign_keys=classlist_id, backref='classlist')


    def __init__(
        self, email, password, first_name, middle_name, last_name, section_code='', present_count=0, late_count=0, absent_count=0, is_confirmed=False, confirmed_on=None, is_faculty=False
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
        self.section_code = section_code
        self.present_count = present_count
        self.late_count = late_count
        self.absent_count = absent_count
        
    def __repr__(self):
        return f"<email {self.email}>"
