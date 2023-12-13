from datetime import datetime
from flask_login import UserMixin
from src import bcrypt, db
from sqlalchemy import Enum, func
import enum
from sqlalchemy.ext.hybrid import hybrid_method

class Status(enum.Enum):
    PRESENT = 'PRESENT'
    ABSENT = 'ABSENT'
    LATE = 'LATE'

class Semester(enum.Enum):
    FIRST = 'FIRST'
    SECOND = 'SECOND'
    SUMMER = 'SUMMER'

assoc = db.Table(
    'assoc',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('classlist_id', db.Integer, db.ForeignKey('classlist.id', ondelete='CASCADE')),
)

class ClassList(db.Model):
    __tablename__ = "classlist"
    
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    school_year = db.Column(db.Integer, nullable=False)
    semester = db.Column(Enum(Semester, values_callable=lambda x: [str(e.value) for e in Semester]), nullable=False)
    section_code = db.Column(db.String(100), nullable=False)

    students = db.relationship(
        'User',
        secondary=assoc,
        back_populates='classlists',
        lazy='dynamic'
    )

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_classlist = db.relationship('User', back_populates='classlists')
    faculty_creator = db.relationship('User', back_populates='created_classlists', overlaps="user_classlist")

    attendance_records = db.relationship(
        'Attendance',
        back_populates='classlist',
        cascade='all, delete-orphan',
    )

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    attendance_status = db.Column(Enum(Status, values_callable=lambda x: [str(e.value) for e in Status]), nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_attendance = db.relationship('User', back_populates='classlist_attendance')

    classlist_id = db.Column(db.Integer, db.ForeignKey('classlist.id'), nullable=False)
    classlist = db.relationship('ClassList', back_populates='attendance_records')

class User(db.Model,UserMixin):
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
    present_count = db.Column(db.Integer, nullable=True)
    late_count = db.Column(db.Integer, nullable=True)
    absent_count = db.Column(db.Integer, nullable=True)

    classlists = db.relationship(
        'ClassList',
        secondary='assoc',
        back_populates='students',
        cascade='all, delete-orphan',
        single_parent=True,
        lazy='dynamic'
    )

    classlist_attendance = db.relationship('Attendance', back_populates='user_attendance')
    created_classlists = db.relationship('ClassList', back_populates='faculty_creator', overlaps="user_classlist")
    
    def __init__(
        self, email, password, first_name, middle_name, last_name, present_count=0, late_count=0, absent_count=0, is_confirmed=False, confirmed_on=None, is_faculty=False
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
        self.present_count = present_count
        self.late_count = late_count
        self.absent_count = absent_count

    def __repr__(self):
        return f"<email {self.email}>"