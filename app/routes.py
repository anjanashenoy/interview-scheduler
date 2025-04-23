from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
from .models import *
from . import db
from . import login_manager
import random
from flask import jsonify

main = Blueprint('main', __name__)
northwestern_external_engine = create_engine('postgresql://postgres:cis498123@34.75.162.71:5432/postgres')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) 
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if current_user.is_authenticated:
            logout_user()
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    context = {}

    if current_user.user_type == 'recruiter':
        jobs = Job.query.filter_by(recruiter=current_user.recruiter).all()
        interview_slots = InterviewSlot.query.all()
        context['name'] = current_user.recruiter.name
        context['jobs'] = jobs
        context['interview_slots'] = interview_slots
        dashboard = 'recruiter.html'
    elif current_user.user_type == 'student':
        try:
            with northwestern_external_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT full_name FROM student WHERE university_email = :email"),
                    {"email": current_user.email}
                )
                row = result.fetchone()
                if row:
                    context['name'] = row[0]
        except Exception as e:
            flash("Failed to fetch student name.", 'warning')
        page = request.args.get('page', 1, type=int)
        context['jobs'] = Job.query.paginate(page=page, per_page=3)
        dashboard = 'student.html'

    return render_template(dashboard, **context)

@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    universities = University.query.all()
    companies = Company.query.all()

    if request.method == 'POST':
        role = request.form.get('role')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        if role == 'student':
            university_id = request.form.get('university_id')
            university_email = request.form.get('university_email')

            try:
                with northwestern_external_engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT * FROM student WHERE university_email = :email"),
                        {"email": university_email}
                    )
                    external_student = result.fetchone()
                    if external_student:
                        name = external_student[2]
            except Exception as e:
                flash(str(e), 'danger')
                return redirect(url_for('main.register'))

            if not external_student:
                flash("Student not found in university system.", 'danger')
                return redirect(url_for('main.register'))

            new_user = User(email=university_email, password=hashed_password, user_type=role)
            db.session.add(new_user)
            db.session.flush()

            student = Student(user_id=new_user.id, university_id=university_id)
            db.session.add(student)

        elif role == 'recruiter':
            company_id = request.form.get('company_id')
            name = request.form.get('name')
            company_email = request.form.get('company_email')

            if User.query.filter_by(email=company_email).first():
                flash("Email already in use.", 'danger')
                return redirect(url_for('main.register'))

            new_user = User(email=company_email, password=hashed_password, user_type=role)
            db.session.add(new_user)
            db.session.flush()

            recruiter = Recruiter(user_id=new_user.id, company_id=company_id, name=name)
            db.session.add(recruiter)

        else:
            flash("Invalid role selected.", 'danger')
            return redirect(url_for('main.register'))

        try:
            db.session.commit()
            flash("Account created successfully. Please login.", 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash("Something went wrong during registration. Please try again.", 'danger')
            return redirect(url_for('main.register'))

    return render_template('register.html', universities=universities, companies=companies)

@main.route('/jobs/create', methods=['POST'])
@login_required
def create_job():
    position = request.form['position']
    description = request.form['description']
    job_type = request.form['job_type']
    location = request.form['location']
    time_slots = request.form.getlist('time_slots[]')

    recruiter_id = current_user.id

    new_job = Job(
        recruiter_id=recruiter_id,
        position=position,
        description=description,
        job_type=job_type,
        location=location
    )
    db.session.add(new_job)
    db.session.flush()  

    for slot in time_slots:
        meeting_id = ''.join([str(random.randint(0, 9)) for _ in range(13)])
        interview_slot = InterviewSlot(
            job_id=new_job.id,
            datetime=slot,
            student_id=None,
            status=InterviewStatus.available.value,
            next_steps=None,
            meeting_id=meeting_id
        )
        db.session.add(interview_slot)

    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    Job.query.filter_by(id=job_id).delete()
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route('/jobs/<int:job_id>/edit', methods=['POST'])
@login_required
def edit_job(job_id):
    job = Job.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()

    job.position = request.form['position']
    job.description = request.form['description']
    job.job_type = request.form['job_type']
    job.location = request.form['location']

    # Get the current interview slots for this job
    current_slots = InterviewSlot.query.filter_by(job_id=job_id).all()
    current_slot_ids = {slot.id for slot in current_slots}

    # Get the new slots from the form
    time_slots = request.form.getlist('time_slots[]')
    new_slot_ids = set()

    # Add new slots
    for slot in time_slots:
        # Check if this slot is a new slot (not already in the current slots)
        if slot not in {s.datetime for s in current_slots}:  
            meeting_id = ''.join([str(random.randint(0, 9)) for _ in range(13)])
            interview_slot = InterviewSlot(
                job_id=job.id,
                datetime=slot,
                student_id=None,
                status=InterviewStatus.available.value,
                next_steps=None,
                meeting_id=meeting_id
            )
            db.session.add(interview_slot)
    
    # Remove deleted slots
    for slot in current_slots:
        # If the current slot is not in the new list, delete it
        if slot.datetime not in time_slots:
            db.session.delete(slot)

    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route('/get_interview_slots/<int:job_id>', methods=['GET'])
def get_interview_slots(job_id):
    # Query for interview slots with the specified job_id
    interview_slots = InterviewSlot.query.filter_by(job_id=job_id).all()

    # Serialize the interview slots into a list of dictionaries
    serialized_slots = [serialize_slot(slot) for slot in interview_slots]

    return jsonify(serialized_slots)

def serialize_slot(slot):
    return {
        'id': slot.id,
        'job_id': slot.job_id,
        'status': slot.status,
        'start_time': slot.datetime.isoformat(), 
    }