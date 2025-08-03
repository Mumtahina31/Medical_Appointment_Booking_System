from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_strong_secret_key_here"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient' or 'doctor'
    full_name = db.Column(db.String(150))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="Pending")

# Initialize database
with app.app_context():
    db.create_all()
    if not User.query.first():  # Create sample data if empty
        doctors = [
            User(username='dr_smith', password='pass1', role='doctor', full_name='Dr. John Smith'),
            User(username='dr_jones', password='pass2', role='doctor', full_name='Dr. Sarah Jones')
        ]
        patient = User(username='patient1', password='pass1', role='patient', full_name='Michael Brown')
        db.session.add_all(doctors + [patient])
        db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, password=password, role=role).first()
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            if role == 'patient':
                return redirect(url_for('patient_dashboard'))
            else:
                return redirect(url_for('doctor_dashboard'))
        
        return render_template('login.html', role=role, error="Invalid credentials")
    
    return render_template('login.html', role=role)

@app.route('/patient/dashboard')
def patient_dashboard():
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('index'))
    
    patient = User.query.get(session['user_id'])
    appointments = Appointment.query.filter_by(patient_id=session['user_id'])\
        .join(User, Appointment.doctor_id == User.id)\
        .add_columns(User.full_name)\
        .all()
    
    return render_template('patient_dashboard.html', 
                         patient=patient,
                         appointments=appointments)

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'role' not in session or session['role'] != 'doctor':
        return redirect(url_for('index'))
    
    appointments = Appointment.query.filter_by(doctor_id=session['user_id'])\
        .join(User, Appointment.patient_id == User.id)\
        .add_columns(User.full_name)\
        .all()
    
    return render_template('doctor_appointments.html',
                         appointments=appointments)

@app.route('/view_doctors')
def view_doctors():
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('index'))
    
    doctors = User.query.filter_by(role='doctor').all()
    return render_template('view_doctors.html', doctors=doctors)

@app.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('index'))
    
    doctor = User.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        appointment = Appointment(
            patient_id=session['user_id'],
            doctor_id=doctor_id,
            date=request.form['date'],
            time=request.form['time'],
            status="Pending"
        )
        db.session.add(appointment)
        db.session.commit()
        return redirect(url_for('appointment_status', appointment_id=appointment.id))
    
    return render_template('appointment_form.html', doctor=doctor)

@app.route('/appointment_status/<int:appointment_id>')
def appointment_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if session['user_id'] not in [appointment.patient_id, appointment.doctor_id]:
        return "Unauthorized", 403
    
    doctor = User.query.get(appointment.doctor_id) if session['role'] == 'patient' else None
    patient = User.query.get(appointment.patient_id) if session['role'] == 'doctor' else None
    
    return render_template('appointment_status.html',
                         appointment=appointment,
                         doctor=doctor,
                         patient=patient)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)