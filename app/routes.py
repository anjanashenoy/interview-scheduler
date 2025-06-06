from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text, or_
from .models import *
from . import db
from . import login_manager
import random
from flask import jsonify
from datetime import datetime, timedelta
from .external_dbs import external_engines
from itsdangerous import URLSafeSerializer
from sqlalchemy import or_, and_

main = Blueprint('main', __name__)
northwestern_external_engine = external_engines['Northwestern University']
umd_external_engine = external_engines['University of Maryland']

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

@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    # get all universities and companies to populate form drop downs
    universities = University.query.all()
    companies = Company.query.all()

    if request.method == 'POST':
        role = request.form.get('role')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        # handle student registration
        if role == 'student':
            university_id = request.form.get('university_id')
            university_email = request.form.get('university_email')
            university = University.query.get(university_id).name

            # check to see student isn't already registered
            if User.query.filter_by(email=university_email).first():
                flash("Email already in use.", 'danger')
                return redirect(url_for('main.register'))

            # connect to external db to verify student exists
            try:
                with external_engines[university].connect() as conn:
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

            # create and add the new student to app db
            new_user = User(email=university_email, password=hashed_password, user_type=role)
            db.session.add(new_user)
            db.session.flush()

            student = Student(user_id=new_user.id, university_id=university_id)
            db.session.add(student)

        # handle recruiter registration
        elif role == 'recruiter':
            company_id = request.form.get('company_id')
            name = request.form.get('name')
            company_email = request.form.get('company_email')
            
            # check to see if recruiter is not already registered
            if User.query.filter_by(email=company_email).first():
                flash("Email already in use.", 'danger')
                return redirect(url_for('main.register'))

            # create and add new recruiter to app db
            new_user = User(email=company_email, password=hashed_password, user_type=role)
            db.session.add(new_user)
            db.session.flush()

            recruiter = Recruiter(user_id=new_user.id, company_id=company_id, name=name)
            db.session.add(recruiter)
        else:
            flash("Invalid role selected.", 'danger')
            return redirect(url_for('main.register'))

        try:
            # commit new user to app db
            db.session.commit()
            flash("Account created successfully. Please login.", 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            # rollback in case of errors
            db.session.rollback()
            flash("Something went wrong during registration. Please try again.", 'danger')
            return redirect(url_for('main.register'))

    return render_template('register.html', universities=universities, companies=companies)

@main.route('/dashboard')
@login_required
def dashboard():
    context = {}

    # Get current time for comparison 
    now = datetime.now()

    # recruiter dashboard context
    if current_user.user_type == 'recruiter':

        # find all interviews assigned to recruiter in database
        jobs = Job.query.filter_by(recruiter=current_user.recruiter).all()
        interviews = (
            InterviewSlot.query
            .join(InterviewSlot.job)
            .filter(Job.recruiter_id == current_user.id)
            .order_by(InterviewSlot.datetime)
            .all()
        )
        context['name'] = current_user.recruiter.name
        context['jobs'] = jobs
        context['interviews'] = interviews

        # check and update scheduled interviews for recruiter
        for slot in interviews:
            if slot.status == 'scheduled' and now > slot.datetime + timedelta(minutes=30):
                slot.status = 'completed'
            elif slot.status == 'available' and now > slot.datetime + timedelta(minutes=30):
                db.session.delete(slot)
            db.session.commit()

        dashboard = 'recruiter.html'

    # student dashboard context
    elif current_user.user_type == 'student':
        # connect to external db to get student details
        university = current_user.student.university.name
        try:
            with external_engines[university].connect() as conn:
                result = conn.execute(
                    text("SELECT full_name FROM student WHERE university_email = :email"),
                    {"email": current_user.email}
                )
                row = result.fetchone()
                if row:
                    context['name'] = row[0]
        except Exception as e:
            flash("Failed to fetch student name.", 'warning')

        # filters from request args
        job_type = request.args.get('job_type')
        location = request.args.get('location')
        keyword = request.args.get('keyword')
        page = request.args.get('page', 1, type=int)

        # base query
        query = Job.query

        # filters
        if job_type:
            query = query.filter_by(job_type=job_type)
        if location:
            query = query.filter_by(location=location)
        if keyword:
            query = query.filter(
                or_(
                    Job.position.ilike(f"%{keyword}%"),
                    Job.description.ilike(f"%{keyword}%")
                )
            )

        # send paginated results to template
        context['jobs'] = query.paginate(page=page, per_page=5)

        # get student interviews
        student_id = current_user.id
        interviews = (
            InterviewSlot.query
            .filter_by(student_id=student_id)
            .order_by(InterviewSlot.datetime)
            .all()
        )

        # check and updated scheduled interviews for student
        for slot in interviews:
            if now > slot.datetime + timedelta(minutes=30):
                slot.status = 'completed'
                db.session.commit()

        context['interviews'] = interviews
        context['job_type'] = job_type
        context['location'] = location
        context['keyword'] = keyword
        dashboard = 'student.html'

    return render_template(dashboard, **context)

@main.route('/jobs/create', methods=['POST'])
@login_required
def create_job():
    # get form values
    position = request.form['position']
    description = request.form['description']
    job_type = request.form['job_type']
    location = request.form['location']
    time_slots = request.form.getlist('time_slots[]')

    recruiter_id = current_user.id

    # create new job model with form values
    new_job = Job(
        recruiter_id=recruiter_id,
        position=position,
        description=description,
        job_type=job_type,
        location=location
    )
    db.session.add(new_job)
    db.session.flush()  

    # create empty interview slots
    for slot in time_slots:
        meeting_id = ''.join([str(random.randint(0, 9)) for _ in range(13)])
        interview_slot = InterviewSlot(
            job_id=new_job.id,
            datetime=slot,
            student_id=None,
            status=InterviewStatus.available.value,
            meeting_id=meeting_id
        )
        db.session.add(interview_slot)

    # add new job and interview slots to app db
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.filter_by(id=job_id, recruiter_id=current_user.id).first_or_404()
    job.delete()
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

    db.session.commit()
    return redirect(url_for('main.job_details', job_id=job.id))

@main.route('/jobs/<int:job_id>')
@login_required
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    interview_slots = InterviewSlot.query.filter_by(job_id=job.id).order_by(InterviewSlot.datetime).all()

    scheduled_slots = InterviewSlot.query.filter_by(student_id=current_user.id, status='scheduled').all()
    scheduled_times = {s.datetime for s in scheduled_slots}

    return render_template(
        'job_details.html',
        job=job,
        interview_slots=interview_slots,
        scheduled_count=len(scheduled_slots),
        scheduled_times=scheduled_times
    )

@main.route('/interviews/add', methods=['POST'])
@login_required
def add_slot(job_id):
    if current_user.user_type != 'recruiter':
        abort(403)
    
    slot = request.form.get('datetime')

    meeting_id = ''.join([str(random.randint(0, 9)) for _ in range(13)])
    interview_slot = InterviewSlot(
        job_id=job_id,
        datetime=slot,
        student_id=None,
        status=InterviewStatus.available.value,
        meeting_id=meeting_id
    )
    db.session.add(interview_slot)
    db.session.commit()
    
    flash('Interview slot added!', 'success')
    return redirect(url_for('main.job_details', job_id=job_id))

@main.route('/interviews/book_slot/<int:slot_id>', methods=['POST'])
@login_required
def book_slot(slot_id):
    slot = InterviewSlot.query.get_or_404(slot_id)

    # confirm availability
    if slot.status != 'available':
        flash('This slot is no longer available.', 'danger')
        return redirect(url_for('main.job_details', job_id=slot.job_id))

    # get current student's scheduled slots
    scheduled_slots = InterviewSlot.query.filter_by(student_id=current_user.id).all()

    # prevent booking multiple slots for the same job
    for s in scheduled_slots:
        if s.job_id == slot.job_id:
            flash("Cannot book multiple interviews for the same job.", 'warning')
            return redirect(url_for('main.job_details', job_id=slot.job_id))

    # prevent scheduling more than 3 active interviews
    if len(scheduled_slots) >= 3:
        flash("You already have 3 scheduled interviews. Please cancel one before booking a new slot.", 'warning')
        return redirect(url_for('main.job_details', job_id=slot.job_id))

    # prevent overlapping interview times
    for s in scheduled_slots:
        if s.datetime == slot.datetime:
            flash("This slot conflicts with another interview you've already scheduled ⏰", 'warning')
            return redirect(url_for('main.job_details', job_id=slot.job_id))

    slot.student_id = current_user.id
    slot.status = 'scheduled'
    db.session.commit()

    flash('Interview slot successfully booked! Good luck!', 'success')
    return redirect(url_for('main.job_details', job_id=slot.job_id))

@main.route('/interviews/cancel_slot/<int:slot_id>', methods=['POST'])
@login_required
def cancel_slot(slot_id):
    slot = InterviewSlot.query.get_or_404(slot_id)

    if slot.student_id != current_user.id and (current_user.user_type != 'recruiter' or slot.job.recruiter_id != current_user.id):
        flash("You cannot cancel an interview that isn't yours.", "danger")
        return redirect(url_for('main.dashboard'))
    
    NextStep.query.filter_by(interview_slot_id=slot_id).delete()

    slot.student_id = None
    slot.status = 'available'
    db.session.commit()

    flash("Interview cancelled successfully.", "success")
    return redirect(request.referrer)

@main.route('/interviews/<int:slot_id>/delete', methods=['POST'])
@login_required
def delete_slot(slot_id):
    slot = InterviewSlot.query.get_or_404(slot_id)

    if current_user.user_type != 'recruiter' or slot.job.recruiter_id != current_user.id:
        abort(403)

    job_id = slot.job_id

    db.session.delete(slot)
    db.session.commit()

    flash('Interview slot successfully deleted.', 'success')
    return redirect(request.referrer)

@main.route("/interview_details/<int:slot_id>", methods=["GET"])
@login_required
def interview_details(slot_id):
    interview = InterviewSlot.query.get_or_404(slot_id)

    is_recruiter_owner = current_user.user_type == 'recruiter' and interview.job.recruiter_id == current_user.id
    is_student_owner = current_user.user_type == 'student' and interview.student_id == current_user.id

    if not (is_recruiter_owner or is_student_owner):
        abort(403)
    
    student = Student.query.get(interview.student_id)
    university_name = student.university.name

    try:
        with external_engines[university_name].connect() as conn:
            result = conn.execute(
                text("SELECT * FROM student WHERE university_email = :email"),
                {"email": interview.student.user.email}
            )
            external_student = result.fetchone()
            if external_student:
                name = external_student[2]
    except Exception as e:
        flash(str(e), 'danger')

    next_steps = NextStep.query.filter_by(interview_slot_id=slot_id).order_by(NextStep.timestamp.desc())
    return render_template('interview_details.html', interview=interview, next_steps=next_steps, name=name)


@main.route("/interview_details/<int:slot_id>/add_next_steps", methods=["POST"])
@login_required
def add_next_steps(slot_id):
    interview = InterviewSlot.query.get_or_404(slot_id)
    next_steps = NextStep(
        interview_slot_id=slot_id,
        content=request.form.get('next_steps')
    )
    db.session.add(next_steps)
    db.session.commit()
    
    return redirect(url_for('main.interview_details', slot_id=slot_id))

@main.route("/calendar", methods=["GET"])
@login_required
def calendar():
    interviews = (
            InterviewSlot.query
            .join(InterviewSlot.job)
            .filter(Job.recruiter_id == current_user.id)
            .order_by(InterviewSlot.datetime.desc())
            .all()
        )
    return render_template('calendar.html', interviews=interviews)

@main.route('/student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def student_profile(student_id):
    if current_user.user_type == 'student' and current_user.id != student_id:
        flash("You can only view your own profile.", "warning")
        return redirect(url_for('main.dashboard'))

    student = Student.query.get(student_id)

    # Handle form submission
    if request.method == 'POST':
        skill_name = request.form.get('skill')
        if skill_name:
            new_skill = Skill(student_id=student.user_id, name=skill_name.strip())
            db.session.add(new_skill)

        exp_title = request.form.get('exp_title')
        exp_company = request.form.get('exp_company')
        exp_description = request.form.get('exp_description')
        exp_start = request.form.get('exp_start')
        exp_end = request.form.get('exp_end')

        if exp_title and exp_start:
            new_exp = Experience(
                student_id=student.user_id,
                title=exp_title.strip(),
                company=exp_company.strip() if exp_company else None,
                description=exp_description.strip() if exp_description else None,
                start_date=exp_start,
                end_date=exp_end if exp_end else None
            )
            db.session.add(new_exp)

        db.session.commit()
        return redirect(url_for('main.student_profile', student_id=student_id))

    context = get_student_profile_context(student_id)
    if not context:
        flash("Unable to load student profile.", "danger")
        return redirect(url_for('main.dashboard'))

    # Add skills and experiences to context
    context["skills"] = Skill.query.filter_by(student_id=student_id).all()
    context["experiences"] = Experience.query.filter_by(student_id=student_id).all()
    return render_template("student_profile.html", **context)

@main.route('/students')
@login_required
def students():
    context = {
        'students': [],
        'total_students': 0,
        'page': request.args.get('page', 1, type=int),
        'total_pages': 0,
        'has_prev': False,
        'has_next': False,
        'per_page': 10,
        'gpa_filter': request.args.get('gpa', ''),
        'major_filter': request.args.get('major', ''),
        'skill_filter': request.args.get('skill', ''),
        'experience_filter': request.args.get('experience', '')
    }

    page = context['page']
    per_page = context['per_page']
    gpa_filter = context['gpa_filter']
    major_filter = context['major_filter']
    skill_filter = context['skill_filter']
    experience_filter = context['experience_filter']

    app_students = User.query.filter_by(user_type="student").all()
    app_student_emails = {student.email for student in app_students}

    if skill_filter:
        skill_matches = Skill.query.filter(Skill.name.ilike(f"%{skill_filter}%")).all()
        skill_emails = {s.student.user.email for s in skill_matches}
        app_student_emails &= skill_emails  # intersect

    if experience_filter:
        exp_matches = Experience.query.filter(or_(
            Experience.title.ilike(f"%{experience_filter}%"),
            Experience.company.ilike(f"%{experience_filter}%"),
            Experience.description.ilike(f"%{experience_filter}%")
        )).all()
        exp_emails = {e.student.user.email for e in exp_matches}
        app_student_emails &= exp_emails  # intersect again

    query = """
        SELECT s.id, s.full_name, s.date_of_birth, s.gpa, s.university_email, m.name AS major_name
        FROM student s
        LEFT JOIN major m ON s.major_id = m.id
        WHERE s.university_email IS NOT NULL
    """

    if gpa_filter:
        query += f" AND s.gpa >= {gpa_filter}"
    if major_filter:
        query += f" AND m.name = '{major_filter}'"

    count_query = "SELECT COUNT(*) FROM (" + query + ") AS total"
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"

    all_students = []

    try:
        for uni_name, engine in external_engines.items():
            with engine.connect() as conn:
                student_result = conn.execute(text(query))
                students = student_result.fetchall()
                all_students.extend(students)

        active_students = [s for s in all_students if s.university_email in app_student_emails]

        total_students = len(active_students)
        total_pages = (total_students + per_page - 1) // per_page

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_students = active_students[start_idx:end_idx]

        context.update({
            'students': paginated_students,
            'total_students': total_students,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        })

    except Exception as e:
        flash("Failed to fetch student data.", "danger")
        print(f"Error: {e}")

    return render_template('student_search.html', **context)

@main.route('/generate-reference', methods=['POST'])
@login_required
def generate_reference():
    if current_user.user_type != 'student':
        flash("Only students can request references.", "danger")
        return redirect(url_for('main.dashboard'))

    ref_name = request.form.get('ref_name')
    ref_email = request.form.get('ref_email')

    existing_refs = Reference.query.filter_by(student_id=current_user.id).count()
    if existing_refs >= 3:
        flash("You’ve reached your 3-reference limit.", "warning")
        return redirect(url_for('main.student_profile', student_id=current_user.id))

    invite_link = generate_reference_invite(current_user.id, ref_name, ref_email)
    context = get_student_profile_context(current_user.id)

    if not context:
        flash("Error loading profile for reference generation.", "danger")
        return redirect(url_for('main.dashboard'))

    context["reference_link"] = invite_link
    return render_template("student_profile.html", **context)

@main.route('/submit-reference/<token>', methods=['GET', 'POST'])
def submit_reference(token):
    s = URLSafeSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except Exception:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for('main.home'))

    student_id = data['student_id']
    ref_name = data['reference_name']
    ref_email = data['reference_email']

    if request.method == 'POST':
        relationship = request.form.get('relationship')
        content = request.form.get('content')
        phone = request.form.get('phone')
        is_private = bool(request.form.get('is_private'))

        new_ref = Reference(
            student_id=student_id,
            name=ref_name,
            email=ref_email,
            relationship=relationship,
            content=content,
            phone=phone,
            is_private=is_private
        )
        db.session.add(new_ref)
        db.session.commit()
        
        # Flash success message
        flash("Thank you! Your reference has been submitted.", "success")
        
        # Redirect back to the same page to show the flash message
        return redirect(url_for('main.submit_reference', token=token))

    return render_template('reference.html', ref_name=ref_name, ref_email=ref_email)

def generate_reference_invite(student_id, ref_name, ref_email):
    s = URLSafeSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps({
        'student_id': student_id,
        'reference_name': ref_name,
        'reference_email': ref_email
    })
    return url_for('main.submit_reference', token=token, _external=True)

def get_student_profile_context(student_id):
    context = {}

    student = User.query.filter_by(id=student_id).first()
    if not student:
        return None

    student_email = student.email
    university = student.student.university.name

    try:
        with external_engines[university].connect() as conn:
            student_result = conn.execute(
                text("""
                    SELECT s.id, s.full_name, s.date_of_birth, s.enrollment_year, 
                           s.gpa, s.university_email, m.name AS major_name
                    FROM student s
                    LEFT JOIN major m ON s.major_id = m.id
                    WHERE s.university_email = :email
                """),
                {"email": student_email}
            )
            student_row = student_result.fetchone()

            if student_row:
                data = student_row._mapping
                context["student"] = {
                    "full_name": data["full_name"],
                    "date_of_birth": data["date_of_birth"],
                    "enrollment_year": data["enrollment_year"],
                    "gpa": data["gpa"],
                    "email": data["university_email"],
                    "major": data["major_name"]
                }

                course_result = conn.execute(
                    text("""
                        SELECT c.course_code, c.name AS course_name, c.department, 
                               c.credits, sc.semester, sc.grade, sc.status
                        FROM student_course sc
                        JOIN course c ON sc.course_id = c.id
                        WHERE sc.student_id = :student_id
                    """),
                    {"student_id": data["id"]}
                )

                context["courses"] = [row._mapping for row in course_result.fetchall()]
                context['name'] = data["full_name"]
                context['references'] = Reference.query.filter_by(student_id=student_id).all()


    except Exception as e:
        print(f"Error loading student profile: {e}")
        return None

    return context
