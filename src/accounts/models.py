from datetime import datetime
from flask_login import UserMixin
from src import bcrypt, db
from sqlalchemy import func, Enum
import enum

class Status(enum.Enum):
    PRESENT = 'PRESENT'
    ABSENT = 'ABSENT'
    LATE = 'LATE'

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    attendance_status = db.Column(Enum(Status), nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    #section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    user = db.relationship('User', backref='attendance')

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    middle_name = db.Column(db.String(150), nullable=True)
    last_name = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    created_on = db.Column(db.DateTime, nullable=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    qr_code = db.Column(db.LargeBinary, nullable=True)

    def __init__(
        self, email, password, first_name, middle_name, last_name, qr_code, is_admin=False, is_confirmed=False, confirmed_on=None
    ):  
        self.email = email
        self.password = bcrypt.generate_password_hash(password)
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.qr_code = qr_code
        self.created_on = datetime.now()
        self.is_admin = is_admin
        self.is_confirmed = is_confirmed
        self.confirmed_on = confirmed_on

    def __repr__(self):
        return f"<email {self.email}>"

