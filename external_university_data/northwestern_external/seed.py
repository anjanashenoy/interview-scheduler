import click
from flask.cli import with_appcontext
from .models import *
from . import db
from datetime import date

@click.command('seed')
@with_appcontext
def seed_command():
    cs = Major(name='Computer Science')
    econ = Major(name='Economics')
    psych = Major(name='Psychology')
    math = Major(name='Mathematics')
    db.session.add_all([cs, econ, psych, math])
    db.session.commit()

    course1 = Course(course_code='CS101', name='Intro to CS', department='CS', credits=4)
    course2 = Course(course_code='CS201', name='Data Structures', department='CS', credits=3)
    course3 = Course(course_code='ECON101', name='Microeconomics', department='Economics', credits=3)
    course4 = Course(course_code='PSYCH101', name='Intro to Psychology', department='Psychology', credits=3)
    course5 = Course(course_code='MATH221', name='Calculus I', department='Math', credits=4)
    db.session.add_all([course1, course2, course3, course4, course5])
    db.session.commit()

    s1 = Student(
        university_email='alice@northwestern.edu',
        full_name='Alice Johnson',
        date_of_birth=date(2002, 4, 15),
        enrollment_year=2020,
        major_id=cs.id,
        gpa=3.7
    )

    s2 = Student(
        university_email='bob@northwestern.edu',
        full_name='Bob Smith',
        date_of_birth=date(2001, 9, 10),
        enrollment_year=2019,
        major_id=econ.id,
        gpa=3.4
    )

    s3 = Student(
        university_email='carol@northwestern.edu',
        full_name='Carol Martinez',
        date_of_birth=date(2003, 1, 5),
        enrollment_year=2021,
        major_id=cs.id,
        gpa=3.9
    )

    s4 = Student(
        university_email='derek@northwestern.edu',
        full_name='Derek Lee',
        date_of_birth=date(2000, 11, 23),
        enrollment_year=2018,
        major_id=psych.id,
        gpa=3.2
    )

    s5 = Student(
        university_email='emily@northwestern.edu',
        full_name='Emily Zhao',
        date_of_birth=date(2002, 6, 3),
        enrollment_year=2020,
        major_id=math.id,
        gpa=3.85
    )

    db.session.add_all([s1, s2, s3, s4, s5])
    db.session.commit()

    db.session.add_all([
        # Alice
        StudentCourse(student_id=s1.id, course_id=course1.id, semester='Fall 2020', grade=3.7, status='Completed'),
        StudentCourse(student_id=s1.id, course_id=course2.id, semester='Winter 2021', grade=3.6, status='Completed'),
        StudentCourse(student_id=s1.id, course_id=course4.id, semester='Spring 2021', grade=None, status='In Progress'),

        # Bob
        StudentCourse(student_id=s2.id, course_id=course3.id, semester='Fall 2019', grade=3.4, status='Completed'),
        StudentCourse(student_id=s2.id, course_id=course5.id, semester='Fall 2020', grade=None, status='Withdrawn'),

        # Carol
        StudentCourse(student_id=s3.id, course_id=course1.id, semester='Fall 2021', grade=4.0, status='Completed'),
        StudentCourse(student_id=s3.id, course_id=course2.id, semester='Winter 2022', grade=3.8, status='Completed'),
        StudentCourse(student_id=s3.id, course_id=course3.id, semester='Spring 2022', grade=3.9, status='Completed'),

        # Derek
        StudentCourse(student_id=s4.id, course_id=course4.id, semester='Fall 2018', grade=3.2, status='Completed'),
        StudentCourse(student_id=s4.id, course_id=course3.id, semester='Winter 2019', grade=3.3, status='Completed'),
        StudentCourse(student_id=s4.id, course_id=course5.id, semester='Fall 2021', grade=None, status='In Progress'),

        # Emily
        StudentCourse(student_id=s5.id, course_id=course5.id, semester='Fall 2020', grade=3.9, status='Completed'),
        StudentCourse(student_id=s5.id, course_id=course2.id, semester='Winter 2021', grade=3.8, status='Completed'),
        StudentCourse(student_id=s5.id, course_id=course1.id, semester='Fall 2021', grade=3.9, status='Completed'),
    ])

    db.session.commit()
    print("Seeded sample data.")
