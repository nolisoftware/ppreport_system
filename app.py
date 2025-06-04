from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    is_main_office = db.Column(db.Boolean, default=False)

# Database Models (updated with all columns)
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    district = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(100))
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    submitted_by = db.Column(db.String(80), nullable=False)

def initialize_database():
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        districts = [
            "ወረዳ 1", "ወረዳ 2", "ወረዳ 3", "ወረዳ 4", "ወረዳ 5", 
            "ወረዳ 6", "ወረዳ 7", "ወረዳ 8", "ወረዳ 9", "አሰሊሶ", 
            "ቢዮአዋሌ", "ዋሂል", "ቀልአድ"
        ]
        
        # Main office user
        main_user = User(
            username='main_office',
            password=generate_password_hash('main123'),
            district='Main Office',
            is_main_office=True
        )
        db.session.add(main_user)
        
        # District users
        for i, district in enumerate(districts, 1):
            username = f'woreda{i}' if i <= 9 else district.lower()
            user = User(
                username=username,
                password=generate_password_hash(f'woreda{i}pass'),
                district=district,
                is_main_office=False
            )
            db.session.add(user)
        
        db.session.commit()
        print("Database initialized with all required columns!")

# Initialize database
initialize_database()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['district'] = user.district
            session['is_main_office'] = user.is_main_office
            flash('በትክክል ገብተዋል!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('ያልተሳካ መግቢያ! እባክዎ የተጠቃሚ ስም እና የይለፍ ቃል ይፈትሹ', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('በትክክል ወጥተዋል!', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['is_main_office']:
        reports = Report.query.order_by(Report.submitted_at.desc()).all()
    else:
        reports = Report.query.filter_by(district=session['district']).order_by(Report.submitted_at.desc()).all()
    
    return render_template('dashboard.html', reports=reports)
def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/submit_report', methods=['GET', 'POST'])
def submit_report():
    if 'user_id' not in session or session['is_main_office']:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        year = request.form['year']
        quarter = request.form['quarter']
        title = request.form['title']
        description = request.form['description']
        
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('እባክዎ ፋይል ይምረጡ', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('እባክዎ ፋይል ይምረጡ', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{session['district']}_{year}_{quarter}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Check if report already exists
            existing_report = Report.query.filter_by(
                district=session['district'],
                year=year,
                quarter=quarter
            ).first()
            
            if existing_report:
                flash('ለዚህ ሩብ ዓመት የቀረበ ሪፖርት አለ!', 'warning')
                return redirect(url_for('dashboard'))
            
            report = Report(
                district=session['district'],
                year=year,
                quarter=quarter,
                title=title,
                description=description,
                filename=filename,
                submitted_by=session['username']
            )
            db.session.add(report)
            db.session.commit()
            flash('ሪፖርቱ በትክክል ቀርቧል!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('የማይፈቀድ ፋይል አይነት! እባክዎ PDF, Word ወይም Excel ፋይል ይምረጡ', 'danger')
    
    return render_template('submit_report.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/view_report/<int:report_id>')
def view_report(report_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    report = Report.query.get_or_404(report_id)
    
    if not session['is_main_office'] and report.district != session['district']:
        flash('ይህን ሪፖርት ለማየት ፈቃድ የለዎትም!', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('view_report.html', report=report)

if __name__ == '__main__':
    app.run(debug=True)