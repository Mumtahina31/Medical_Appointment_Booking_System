from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Ensure you change this for production!

# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient' or 'doctor'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="Pending")

# Create DB tables
# Initialize database manually
def create_tables():
    with app.app_context():
        db.create_all()
        # Create sample doctors if none exist
        if not User.query.filter_by(role='doctor').first():
            doc1 = User(username='doc1', password='pass1', role='doctor')
            doc2 = User(username='doc2', password='pass2', role='doctor')
            db.session.add_all([doc1, doc2])
            db.session.commit()

# Now, manually call create_tables() before starting the app
create_tables()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if request.method == 'POST':
        # Retrieve the username and password from the form
        username = request.form['username']
        password = request.form['password']
        
        # Query the database for the user matching the given credentials and role
        user = User.query.filter_by(username=username, password=password, role=role).first()
        
        if user:
            # Store user info in the session to keep track of logged-in user
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Redirect based on the role of the user
            if role == 'patient':
                return redirect(url_for('view_doctors'))  # Redirect to the doctors view for patients
            else:
                return redirect(url_for('doctor_appointments'))  # Redirect to doctor appointments page for doctors
        else:
            # If user not found or credentials are invalid, show an error message
            return render_template('login.html', role=role, error="Invalid credentials")
    
    # Handle GET request and show the login page
    return render_template('login.html', role=role)

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
        date = request.form['date']
        appointment = Appointment(patient_id=session['user_id'], doctor_id=doctor_id, date=date)
        db.session.add(appointment)
        db.session.commit()
        return redirect(url_for('appointment_status', appointment_id=appointment.id))
    return render_template('appointment_form.html', doctor=doctor)

@app.route('/appointment_status/<int:appointment_id>')
def appointment_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if 'user_id' not in session or (session['user_id'] not in [appointment.patient_id, appointment.doctor_id]):
        return "Unauthorized", 403
    return render_template('appointment_status.html', appointment=appointment)

@app.route('/doctor/appointments')
def doctor_appointments():
    if 'role' not in session or session['role'] != 'doctor':
        return redirect(url_for('index'))
    appointments = Appointment.query.filter_by(doctor_id=session['user_id']).all()
    return render_template('doctor_appointments.html', appointments=appointments)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Now, manually call create_tables() before starting the app
if __name__ == '__main__':
    app.run(debug=True)
