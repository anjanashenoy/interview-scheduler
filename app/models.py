from . import db
from flask_login import UserMixin
import enum

class InterviewStatus(enum.Enum):
    available = 'available'
    scheduled = 'scheduled'
    completed = 'completed'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(4096), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    student = db.relationship('Student', backref='user', uselist=False)
    recruiter = db.relationship('Recruiter', backref='user', uselist=False)

class Student(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'))
    university = db.relationship('University', backref='students')
    references = db.relationship('Reference', backref='student', lazy=True)

class Recruiter(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    company = db.relationship('Company', backref='recruiters')
    jobs = db.relationship('Job', backref='recruiter', lazy=True)

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class Reference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.user_id'))
    content = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(100))
    relationship = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter.user_id'))
    position = db.Column(db.String(100))
    job_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    location = db.Column(db.String(50))
    interview_slots = db.relationship('InterviewSlot', backref='job', lazy=True)

class InterviewSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.user_id'), nullable=True)
    datetime = db.Column(db.DateTime, nullable=False)
    meeting_id = db.Column(db.String(15), nullable=False)

    status = db.Column(db.String(20), default=InterviewStatus.available)

    student = db.relationship('Student', backref='interview_slot')
    next_steps = db.relationship('NextStep', back_populates='interview_slot', cascade='all, delete-orphan', order_by='NextStep.timestamp')

class NextStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interview_slot_id = db.Column(db.Integer, db.ForeignKey('interview_slot.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    interview_slot = db.relationship('InterviewSlot', back_populates='next_steps')