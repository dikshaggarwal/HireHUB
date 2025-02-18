import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, url_for, flash, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask and SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobs.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    jobs = db.relationship('Job', backref='company', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    location = db.Column(db.String(100))
    salary_range = db.Column(db.String(50))
    job_type = db.Column(db.String(50))
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    requirements = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    jobs = Job.query.order_by(Job.posted_date.desc()).all()
    return render_template('index.html', jobs=jobs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        user = User.query.filter_by(email=email, role=role).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        mobile = request.form.get('mobile')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, mobile=mobile)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job)

@app.route('/company/<int:company_id>')
def company_profile(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template('company_profile.html', company=company)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)  # Forbidden access
        return f(*args, **kwargs)
    return decorated_function

@app.route('/post-job', methods=['GET', 'POST'])
@login_required
@admin_required
def post_job():
    if request.method == 'POST':
        data = request.get_json()
        job = Job(**data)
        db.session.add(job)
        db.session.commit()
        return jsonify({"message": "Job posted successfully"})

    companies = Company.query.all()
    return render_template('post_job.html', companies=companies)

@app.route('/update-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        job.title = request.form.get('title')
        job.description = request.form.get('description')
        job.location = request.form.get('location')
        job.salary_range = request.form.get('salary_range')
        job.job_type = request.form.get('job_type')
        job.requirements = request.form.get('requirements')
        db.session.commit()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('job_detail', job_id=job.id))

    companies = Company.query.all()
    return render_template('update_job.html', job=job, companies=companies)

@app.route('/delete-job/<int:job_id>', methods=['POST'])
@login_required
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/search')
def search_jobs():
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '').strip()
    
    # Start with base query
    query = Job.query
    
    # Apply filters if we have search terms
    if keyword:
        keyword = f"%{keyword}%"
        query = query.filter(
            db.or_(
                Job.title.ilike(keyword),
                Job.description.ilike(keyword),
                Job.requirements.ilike(keyword),
                Job.company.has(Company.name.ilike(keyword))  # Search company names too
            )
        )
    
    if location:
        location = f"%{location}%"
        query = query.filter(Job.location.ilike(location))
    
    # Execute query with ordering
    jobs = query.order_by(Job.posted_date.desc()).all()
    
    # If this is an AJAX request, return only the jobs list partial
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('_jobs_list.html', jobs=jobs)
    
    # Otherwise return the full page
    return render_template('index.html', jobs=jobs, 
                         search_keyword=keyword.strip('%') if keyword else '',
                         search_location=location.strip('%') if location else '')
    
@app.route('/companies')
@login_required
@admin_required
def list_companies():
    companies = Company.query.all()
    return render_template('companies.html', companies=companies)

@app.route('/add-company', methods=['GET', 'POST'])
@login_required
@admin_required
def add_company():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        logo_url = request.form.get('logo_url')

        # Add to database
        new_company = Company(
            name=name,
            description=description,
            logo_url=logo_url
        )
        db.session.add(new_company)
        db.session.commit()

        # Update mock_data.py
        try:
            with open('mock_data.py', 'r') as file:
                content = file.read()
            
            # Find the COMPANY_DATA list
            company_data_start = content.find('COMPANY_DATA = [')
            if company_data_start != -1:
                # Find the position just before the closing bracket
                bracket_pos = content.find(']', company_data_start)
                if bracket_pos != -1:
                    # Create new company entry
                    new_entry = f"""    {{"name": "{name}","description": "{description}","logo_url": "{logo_url}"}},\n"""
                    
                    # Insert the new entry before the closing bracket
                    updated_content = (
                        content[:bracket_pos] + 
                        new_entry + 
                        content[bracket_pos:]
                    )
                    
                    with open('mock_data.py', 'w') as file:
                        file.write(updated_content)
                        
            flash('Company added successfully!', 'success')
            return redirect(url_for('list_companies'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding company: {str(e)}', 'danger')
            return redirect(url_for('add_company'))

    return render_template('add_company.html')
# Add these error handlers after the routes
@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html',
                         error_code=403,
                         error_message='Access Forbidden',
                         error_description='You do not have permission to access this resource.'), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html',
                         error_code=404,
                         error_message='Page Not Found',
                         error_description='The requested page could not be found.'), 404


# Initialize database and add mock data
with app.app_context():
    from mock_data import COMPANY_DATA, JOB_DATA

    db.create_all()
    # Initialize mock data if database is empty
    if not Company.query.first():
        for company_data in COMPANY_DATA:
            company = Company(**company_data)
            db.session.add(company)
        db.session.commit()

        for job_data in JOB_DATA:
            job = Job(**job_data)
            db.session.add(job)
        db.session.commit()

    # Create admin user if not exists
    if not User.query.filter_by(role="admin").first():
        admin_user = User(
            name="Admin",
            email="admin@gmail.com",
            mobile="1234567890",
            role="admin"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created with email: admin@gmail.com and password: admin123")

if __name__ == "__main__":
    app.run(debug=True)