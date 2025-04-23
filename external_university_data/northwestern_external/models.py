from . import db

class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.Integer, primary_key=True)
    university_email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date)
    enrollment_year = db.Column(db.Integer)
    major_id = db.Column(db.Integer, db.ForeignKey('major.id'))
    gpa = db.Column(db.Float)
    courses = db.relationship('StudentCourse', backref='student', lazy=True)

class Major(db.Model):
    __tablename__ = 'major'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    students = db.relationship('Student', backref='major', lazy=True)


class Course(db.Model):
    __tablename__ = 'course'

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    credits = db.Column(db.Integer)
    students = db.relationship('StudentCourse', backref='course', lazy=True)


class StudentCourse(db.Model):
    __tablename__ = 'student_course'

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    semester = db.Column(db.String(20))  
    grade = db.Column(db.Float)
    status = db.Column(db.String(20))  
