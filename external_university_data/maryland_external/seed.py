import click
from flask.cli import with_appcontext
from .models import *
from . import db
from datetime import date

@click.command('seed')
@with_appcontext
def seed_command():
    # Majors
    ce = Major(name='Computer Engineering')
    isci = Major(name='Information Science')
    me = Major(name='Mechanical Engineering')
    ee = Major(name='Electrical Engineering')
    phys = Major(name='Physics')
    db.session.add_all([ce, isci, me, ee, phys])
    db.session.commit()

    # Courses
    course1 = Course(course_code='CMSENG131', name='Intro to Computer Engineering', department='Computer Engineering', credits=3)
    course2 = Course(course_code='CMENG132', name='Data Structures', department='Computer Engineering', credits=4)
    course3 = Course(course_code='MECENG232', name='Thermodynamics', department='Mechanical Engineering', credits=3)
    course4 = Course(course_code='ELENG205', name='Circuit Theory', department='Electrical Engineering', credits=3)
    course5 = Course(course_code='PHYS200', name='Advance Physics', department='Sciences', credits=3)
    db.session.add_all([course1, course2, course3, course4, course5])
    db.session.commit()

    # Students
    s1 = Student(
        university_email='maya@umd.edu',
        full_name='Maya Smith',
        date_of_birth=date(2002, 3, 14),
        enrollment_year=2021,
        major_id=ce.id,
        gpa=3.75
    )

    s2 = Student(
        university_email='jamal@umd.edu',
        full_name='Jamal Lee',
        date_of_birth=date(2001, 7, 8),
        enrollment_year=2020,
        major_id=me.id,
        gpa=3.65
    )

    s3 = Student(
        university_email='rina@umd.edu',
        full_name='Rina Patel',
        date_of_birth=date(2003, 1, 20),
        enrollment_year=2022,
        major_id=isci.id,
        gpa=3.90
    )

    s4 = Student(
        university_email='carlos@umd.edu',
        full_name='Carlos Martinez',
        date_of_birth=date(2000, 12, 1),
        enrollment_year=2019,
        major_id=phys.id,
        gpa=3.55
    )

    s5 = Student(
        university_email='elena@umd.edu',
        full_name='Elena Novak',
        date_of_birth=date(2001, 5, 18),
        enrollment_year=2020,
        major_id=ee.id,
        gpa=3.80
    )

    db.session.add_all([s1, s2, s3, s4, s5])
    db.session.commit()

    # Student Courses
    db.session.add_all([
        # Maya
        StudentCourse(student_id=s1.id, course_id=course1.id, semester='Fall 2021', grade=3.7, status='Completed'),
        StudentCourse(student_id=s1.id, course_id=course2.id, semester='Spring 2022', grade=3.6, status='Completed'),

        # Jamal
        StudentCourse(student_id=s2.id, course_id=course3.id, semester='Fall 2020', grade=3.4, status='Completed'),

        # Rina
        StudentCourse(student_id=s3.id, course_id=course1.id, semester='Fall 2022', grade=4.0, status='Completed'),
        StudentCourse(student_id=s3.id, course_id=course2.id, semester='Winter 2023', grade=3.8, status='In Progress'),

        # Carlos
        StudentCourse(student_id=s4.id, course_id=course5.id, semester='Spring 2021', grade=3.5, status='Completed'),

        # Elena
        StudentCourse(student_id=s5.id, course_id=course4.id, semester='Fall 2020', grade=3.8, status='Completed'),
        StudentCourse(student_id=s5.id, course_id=course3.id, semester='Spring 2021', grade=3.7, status='In Progress'),
    ])
    
    db.session.commit()
    print("UMD external DB successfully seeded.")
