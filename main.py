from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from flask_login import login_required, current_user
import random
# Flask App Initialization
app = Flask(__name__, template_folder="templates")
app.secret_key = "quiz_master_secret_key"

# Database Configuration
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{os.path.join(base_dir, "quiz.sqlite3")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    quiz_scores = db.relationship("Score", back_populates="user", cascade="all, delete-orphan")

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chapters = db.relationship("Chapter", back_populates='subject', cascade="all, delete-orphan")

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.relationship('Subject', back_populates='chapters')
    quizzes = db.relationship("Quiz", back_populates='chapter', cascade="all, delete-orphan")

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.String(5), nullable=False)  # Format: HH:MM
    remarks = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chapter = db.relationship('Chapter', back_populates='quizzes')
    questions = db.relationship("Question", back_populates='quiz', cascade="all, delete-orphan")
    scores = db.relationship("Score", back_populates='quiz', cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', or 'D'
    quiz = db.relationship('Quiz', back_populates='questions')

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    total_scored = db.Column(db.Float, nullable=False)
    quiz = db.relationship('Quiz', back_populates='scores')
    user = db.relationship('User', back_populates='quiz_scores')

# Initialize DB and Create Admin
def create_admin():
    if not User.query.filter_by(email="admin@quizmaster.com").first():
        admin = User(
            username="admin",
            email="admin@quizmaster.com",
            password=generate_password_hash("admin123"),
            fullname="Admin User",
            dob="01-01-1990",
            qualification="System Administrator",
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

with app.app_context():
    db.create_all()
    create_admin()

# Authentication middleware function
def admin_required(route_function):
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            flash("Admin login required", "danger")
            return redirect(url_for("admin_login"))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

def user_required(route_function):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("User login required", "danger")
            return redirect(url_for("user_login"))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

# ROUTES
@app.route("/")
def home():
    return render_template("index.html")

# Auth Routes
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "admin" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        admin = User.query.filter_by(email=email, is_admin=True).first()
        if admin and check_password_hash(admin.password, password):
            session["admin"] = email
            session["admin_id"] = admin.id
            flash("Admin login successful", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials", "danger")

    return render_template("admin_login.html")

@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if "user" in session:
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, is_admin=False).first()
        if user and check_password_hash(user.password, password):
            session["user"] = email
            session["user_id"] = user.id
            flash("Login successful", "success")
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("user_login.html")

@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        fullname = request.form["fullname"]
        qualification = request.form["qualification"]
        dob = request.form["dob"]

        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or email already exists", "danger")
            return redirect(url_for("user_register"))

        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            fullname=fullname,
            qualification=qualification,
            dob=dob,
            is_admin=False
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("user_login"))
        
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("home"))

# Admin Routes
@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "total_subjects": Subject.query.count(),
        "total_chapters": Chapter.query.count(),
        "total_quizzes": Quiz.query.count(),
        "total_users": User.query.filter_by(is_admin=False).count()
    }
    subjects = Subject.query.order_by(Subject.created_at.desc()).all()
    return render_template("admin_dashboard.html", stats=stats, subjects=subjects)

# Admin Subject Routes
@app.route("/admin/subjects", methods=["GET"])
@admin_required
def admin_subjects():
    subjects = Subject.query.order_by(Subject.created_at.desc()).all()
    return render_template("admin_subjects.html", subjects=subjects)

@app.route("/admin/subjects/add", methods=["GET", "POST"])
@admin_required
def add_subject():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        
        # Check if subject already exists
        existing_subject = Subject.query.filter_by(name=name).first()
        if existing_subject:
            flash("Subject already exists", "danger")
            return redirect(url_for("add_subject"))
        
        # Create new subject
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        
        flash("Subject added successfully", "success")
        return redirect(url_for("admin_subjects"))
        
    return render_template("add_subject.html")

@app.route("/admin/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        
        # Check if another subject with same name exists
        existing_subject = Subject.query.filter(Subject.name == name, Subject.id != subject_id).first()
        if existing_subject:
            flash("Another subject with this name already exists", "danger")
            return redirect(url_for("edit_subject", subject_id=subject_id))
        
        subject.name = name
        subject.description = description
        db.session.commit()
        
        flash("Subject updated successfully", "success")
        return redirect(url_for("admin_subjects"))
        
    return render_template("edit_subject.html", subject=subject)

@app.route("/admin/subjects/delete/<int:subject_id>")
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    
    flash("Subject deleted successfully", "success")
    return redirect(url_for("admin_subjects"))

# Admin Chapter Routes
@app.route("/admin/chapters/<int:subject_id>")
@admin_required
def admin_chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).order_by(Chapter.created_at.desc()).all()
    return render_template("admin_chapters.html", subject=subject, chapters=chapters)

@app.route("/admin/chapters/add/<int:subject_id>", methods=["GET", "POST"])
@admin_required
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        
        new_chapter = Chapter(
            name=name,
            description=description,
            subject_id=subject_id
        )
        
        db.session.add(new_chapter)
        db.session.commit()
        
        flash("Chapter added successfully", "success")
        return redirect(url_for("admin_chapters", subject_id=subject_id))
        
    return render_template("add_chapter.html", subject=subject)

@app.route("/admin/chapters/edit/<int:chapter_id>", methods=["GET", "POST"])
@admin_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        
        chapter.name = name
        chapter.description = description
        db.session.commit()
        
        flash("Chapter updated successfully", "success")
        return redirect(url_for("admin_chapters", subject_id=chapter.subject_id))
        
    return render_template("edit_chapter.html", chapter=chapter)

@app.route("/admin/chapters/delete/<int:chapter_id>")
@admin_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    subject_id = chapter.subject_id
    
    db.session.delete(chapter)
    db.session.commit()
    
    flash("Chapter deleted successfully", "success")
    return redirect(url_for("admin_chapters", subject_id=subject_id))

# Admin Quiz Routes
@app.route("/admin/quizzes/<int:chapter_id>")
@admin_required
def admin_quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).order_by(Quiz.created_at.desc()).all()
    return render_template("admin_quizzes.html", chapter=chapter, quizzes=quizzes)

@app.route("/admin/quizzes/add/<int:chapter_id>", methods=["GET", "POST"])
@admin_required
def add_quiz(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == "POST":
        title = request.form["title"]
        date_of_quiz = datetime.strptime(request.form["date_of_quiz"], "%Y-%m-%d").date()
        time_duration = request.form["time_duration"]
        remarks = request.form["remarks"]
        
        # Check if quiz already exists
        existing_quiz = Quiz.query.filter_by(chapter_id=chapter_id, title=title).first()
        if existing_quiz:
            flash("Quiz already exists for this chapter", "danger")
            return redirect(url_for("add_quiz", chapter_id=chapter_id))
        
        new_quiz = Quiz(
            title=title,
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            remarks=remarks
        )
        
        db.session.add(new_quiz)
        db.session.commit()
        
        flash("Quiz added successfully", "success")
        return redirect(url_for("admin_quizzes", chapter_id=chapter_id))
        
    return render_template("add_quiz.html", chapter=chapter)
    
# edit quiz form
@app.route("/admin/quizzes/edit/<int:quiz_id>", methods=["GET", "POST"])
@admin_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == "POST":
        quiz.title = request.form["title"]
        quiz.date_of_quiz = datetime.strptime(request.form["date_of_quiz"], "%Y-%m-%d").date()
        quiz.time_duration = request.form["time_duration"]
        quiz.remarks = request.form["remarks"]

        db.session.commit()

        flash("Quiz updated successfully", "success")
        return redirect(url_for("admin_quizzes", chapter_id=quiz.chapter_id))

    return render_template("edit_quiz.html", quiz=quiz)

# delete quiz
@app.route("/admin/quizzes/delete/<int:quiz_id>")
@admin_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter_id

    db.session.delete(quiz)
    db.session.commit()

    flash("Quiz deleted successfully", "success")
    return redirect(url_for("admin_quizzes", chapter_id=chapter_id))

# Admin Question Routes
# View questions in a quiz
@app.route("/admin/questions/<int:quiz_id>")
@admin_required
def admin_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.id.desc()).all()
    return render_template("admin_questions.html", quiz=quiz, questions=questions)

# Add a new question
@app.route("/admin/questions/add/<int:quiz_id>", methods=["GET", "POST"])
@admin_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == "POST":
        question_text = request.form["question_text"]
        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]
        correct_option = request.form["correct_option"]

        # Check if question already exists
        existing_question = Question.query.filter_by(quiz_id=quiz_id, question_text=question_text).first()
        if existing_question:
            flash("This question already exists in the quiz", "danger")
            return redirect(url_for("add_question", quiz_id=quiz_id))

        new_question = Question(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            quiz_id=quiz_id
        )

        db.session.add(new_question)
        db.session.commit()

        flash("Question added successfully", "success")
        return redirect(url_for("admin_questions", quiz_id=quiz_id))

    return render_template("add_question.html", quiz=quiz)

# Edit a question
@app.route("/admin/questions/edit/<int:question_id>", methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == "POST":
        question.question_text = request.form["question_text"]
        question.option_a = request.form["option_a"]
        question.option_b = request.form["option_b"]
        question.option_c = request.form["option_c"]
        question.option_d = request.form["option_d"]
        question.correct_option = request.form["correct_option"]

        db.session.commit()

        flash("Question updated successfully", "success")
        return redirect(url_for("admin_questions", quiz_id=question.quiz_id))

    return render_template("edit_question.html", question=question)

# Delete a question
@app.route("/admin/questions/delete/<int:question_id>")
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id

    db.session.delete(question)
    db.session.commit()

    flash("Question deleted successfully", "success")
    return redirect(url_for("admin_questions", quiz_id=quiz_id))


# Admin Search
@app.route("/admin/search", methods=['GET'])
def admin_search():
    if 'admin' not in session:
        return render_template("error.html", message="Unauthorized access"), 403  # Restrict access to admins

    search_query = request.args.get("q", "").strip()

    if not search_query:
        return render_template("admin_search.html")

    # Searching across multiple models
    users = User.query.filter(User.fullname.like(f"%{search_query}%")).all()
    subjects = Subject.query.filter(Subject.name.like(f"%{search_query}%")).all()
    chapters = Chapter.query.filter(Chapter.name.like(f"%{search_query}%")).all()

    return render_template("admin_search.html", users=users, subjects=subjects, chapters=chapters)


# admin summary
@app.route('/admin/summary')
@admin_required
def admin_summary():
    # Basic statistics
    total_users = User.query.count()
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_quizzes = Quiz.query.count()

    # Get all subjects for detailed analysis
    subjects = Subject.query.all()
    
    # Get quiz count per subject
    quiz_counts = {}
    for subject in subjects:
        quiz_count = 0
        for chapter in subject.chapters:
            quiz_count += len(chapter.quizzes)
        quiz_counts[subject.name] = quiz_count

    # Get chapter count per subject
    chapter_counts = {subject.name: len(subject.chapters) for subject in subjects}
    
    # Get recent users
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    
    # Get recent quiz attempts/scores
    recent_scores = Score.query.order_by(Score.time_stamp_of_attempt.desc()).limit(5).all()
    
    # Generate colors for charts
    colors = []
    for _ in range(len(subjects)):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        colors.append(f"rgba({r}, {g}, {b}, 0.7)")
    
    return render_template("admin_summary.html",
                          total_users=total_users,
                          total_subjects=total_subjects,
                          total_chapters=total_chapters,
                          total_quizzes=total_quizzes,
                          recent_users=recent_users,
                          recent_scores=recent_scores,
                          subjects=subjects,
                          pie_chart_labels=list(quiz_counts.keys()),
                          pie_chart_data=list(quiz_counts.values()),
                          bar_chart_labels=list(chapter_counts.keys()),
                          bar_chart_data=list(chapter_counts.values()),
                          chart_colors=colors)

from functools import wraps
# Custom login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("You need to log in first.", "danger")
            return redirect(url_for("user_login"))
        return f(*args, **kwargs)
    return decorated_function

# User Dashboard
@app.route("/user/dashboard")
@login_required
def user_dashboard():
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("user_login"))
    
    # Fetch available quizzes
    quizzes = Quiz.query.all()

    # Fetch user's past attempts (sorted by most recent)
    scores = Score.query.filter_by(user_id=user.id).order_by(Score.time_stamp_of_attempt.desc()).all()

    return render_template("user_dashboard.html", user=user, quizzes=quizzes, scores=scores)

# User Profile
@app.route("/user/profile", methods=["GET", "POST"])
@login_required
def user_profile():
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("user_login"))

    if request.method == "POST":
        # Updating user profile details
        user.fullname = request.form["fullname"]
        user.dob = request.form["dob"]
        user.qualification = request.form["qualification"]

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating your profile: {str(e)}", "danger")

        return redirect(url_for("user_dashboard"))

    return render_template("user_profile.html", user=user)

##
@app.route("/user/quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    if not questions:
        flash("This quiz has no questions yet.", "warning")
        return redirect(url_for("user_dashboard"))

    if request.method == "POST":
        score = 0
        total_questions = len(questions)
        
        for question in questions:
            selected_option = request.form.get(f"question_{question.id}")
            if selected_option and selected_option == question.correct_option:
                score += 1
        
        # Calculate percentage
        percentage_score = (score / total_questions) * 100
        
        # Save score
        new_score = Score(
            quiz_id=quiz_id,
            user_id=session["user_id"],
            total_scored=percentage_score
        )
        db.session.add(new_score)
        db.session.commit()

        flash(f"You scored {percentage_score:.2f}%.", "success")
        return redirect(url_for("quiz_results", score_id=new_score.id))

    return render_template("take_quiz.html", quiz=quiz, questions=questions)

@app.route("/user/quiz/results/<int:score_id>")
@login_required
def quiz_results(score_id):
    score = Score.query.get_or_404(score_id)
    
    # Make sure the score belongs to the current user
    if score.user_id != session["user_id"]:
        flash("Unauthorized access", "danger")
        return redirect(url_for("user_dashboard"))
    
    quiz = Quiz.query.get(score.quiz_id)
    questions = Question.query.filter_by(quiz_id=score.quiz_id).all()
    
    # Get all attempts for this quiz by this user
    all_attempts = Score.query.filter_by(
        quiz_id=score.quiz_id,
        user_id=session["user_id"]
    ).order_by(Score.id.desc()).all()
    
    return render_template(
        "quiz_results.html", 
        score=score, 
        quiz=quiz, 
        questions=questions,
        all_attempts=all_attempts
    )

@app.route("/user/quiz/history/<int:quiz_id>")
@login_required
def quiz_history(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get all attempts for this quiz by this user
    attempts = Score.query.filter_by(
        quiz_id=quiz_id,
        user_id=session["user_id"]
    ).order_by(Score.id.desc()).all()
    
    # Calculate average score
    average_score = 0
    if attempts:
        total = sum(attempt.total_scored for attempt in attempts)
        average_score = total / len(attempts)
    
    # Get best score
    best_score = max(attempts, key=lambda x: x.total_scored) if attempts else None
    
    return render_template(
        "quiz_history.html", 
        quiz=quiz, 
        attempts=attempts,
        average_score=average_score,
        best_score=best_score
    )

# User Summary with Charts
@app.route("/user/summary")
@login_required
def user_summary():
    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("user_login"))
    
    # Get all user's quiz scores
    scores = Score.query.filter_by(user_id=user.id).all()
    
    # Calculate average score
    total_score = sum(score.total_scored for score in scores) if scores else 0
    avg_score = total_score / len(scores) if scores else 0
    
    # Get subject performance data
    subjects_data = {}
    for score in scores:
        quiz = Quiz.query.get(score.quiz_id)
        chapter = Chapter.query.get(quiz.chapter_id)
        subject = Subject.query.get(chapter.subject_id)
        
        if subject.name not in subjects_data:
            subjects_data[subject.name] = {"scores": [], "count": 0}
        
        subjects_data[subject.name]["scores"].append(score.total_scored)
        subjects_data[subject.name]["count"] += 1
    
    # Calculate average score per subject
    subject_avg_scores = {}
    for subject_name, data in subjects_data.items():
        subject_avg_scores[subject_name] = sum(data["scores"]) / data["count"]
    
    # Generate colors for charts
    colors = []
    for _ in range(len(subject_avg_scores)):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        colors.append(f"rgba({r}, {g}, {b}, 0.7)")
    
    # Count quizzes per subject for pie chart
    subject_quiz_counts = {subject: data["count"] for subject, data in subjects_data.items()}
    
    # Recent quiz attempts
    recent_scores = Score.query.filter_by(user_id=user.id).order_by(Score.time_stamp_of_attempt.desc()).limit(5).all()
    
    return render_template("user_summary.html",
                          user=user,
                          total_quizzes=len(scores),
                          avg_score=avg_score,
                          recent_scores=recent_scores,
                          bar_chart_labels=list(subject_avg_scores.keys()),
                          bar_chart_data=list(subject_avg_scores.values()),
                          pie_chart_labels=list(subject_quiz_counts.keys()),
                          pie_chart_data=list(subject_quiz_counts.values()),
                          chart_colors=colors)

# User Search
@app.route("/user/search", methods=['GET'])
@login_required
def user_search():
    search_query = request.args.get("q", "").strip()
    
    if not search_query:
        return render_template("user_search.html")
    
    # Search for subjects
    subjects = Subject.query.filter(Subject.name.like(f"%{search_query}%")).all()
    
    # Search for chapters
    chapters = Chapter.query.filter(Chapter.name.like(f"%{search_query}%")).all()
    
    # Search for quizzes
    quizzes = Quiz.query.filter(Quiz.title.like(f"%{search_query}%")).all()
    
    return render_template("user_search.html", 
                          subjects=subjects, 
                          chapters=chapters, 
                          quizzes=quizzes,
                          search_query=search_query)


            
if __name__ == "__main__":
    app.run(debug=True)
