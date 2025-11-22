from flask import Flask , render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import or_ 
from config import Config
from datetime import date
from models import db,User,Patient,Doctor,Appointment,Department

def create_app():
    app=Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        ensure_default_admin()

    @app.route('/')
    def home():
        role=session.get("role")

        if role=="admin":
            return redirect(url_for("admin_dashboard"))
        elif role =="doctor":
            return redirect(url_for("doctor_dashboard"))
        elif role =="patient":
            return redirect(url_for("patient_dashboard"))
        
        return redirect(url_for("login"))
    
    @app.route('/register',methods=['GET','POST'])
    def register_patient():
        if request.method =='POST':
            username = request.form['username'].strip()
            password = request.form['password']
            full_name= request.form.get('full_name', '').strip()
            phone=request.form.get('phone','').strip()
            age=request.form.get('age','').strip()
            gender=request.form.get('gender','').strip()
            if not username or not password:
                flash("Username and password are required.")
                return redirect(url_for('register_patient'))
            
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash("Username already taken. Please choose another.")
                return redirect(url_for('register_patient'))
            

            hashed_pw=generate_password_hash(password)
            new_user = User(
                username=username,
                password=hashed_pw,
                role="patient",
                is_active=True
            )
            db.session.add(new_user)
            db.session.flush()

            patient=Patient(
                user_id=new_user.id,
                full_name=full_name or username,
                phone=phone or None,
                age=int(age) if age.isdigit() else None,
                gender=gender or None
            )
            db.session.add(patient)
            db.session.commit()


            flash("Registration successful. Please log in.")
            return redirect(url_for('login'))
        return render_template('register_patient.html')
    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            username=request.form['username'].strip()
            password = request.form['password']

            user = User.query.filter_by(username=username).first()

            if not user or not check_password_hash(user.password,password):
                flash("Invalid username or password.")
                return redirect(url_for('login'))
            
            if not user.is_active:
                flash("Your account is disabled.")
                return redirect(url_for('login'))
            session['user_id']=user.id
            session['username']=user.username
            session['role']=user.role

            if user.role=="admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role=="doctor":
                return redirect(url_for("doctor_dashboard"))
            else:
                return redirect(url_for("patient_dashboard"))
            
        return render_template("login.html")
    @app.route('/admin/doctors/add', methods=['GET','POST'])
    def admin_add_doctor():
        if session.get('role') !="admin":
            return redirect(url_for('login'))
        departments = Department.query.all()

        if request.method == 'POST':
            username=request.form['username'].strip()
            password=request.form['password']
            full_name=request.form['full_name'].strip()
            phone=request.form.get('phone')
            dept_id=request.form.get('department')

            new_user=User(
                username=username,
                password=generate_password_hash(password),
                role="doctor",
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()

            doctor=Doctor(
                user_id=new_user.id,
                full_name=full_name,
                phone=phone,
                department_id=dept_id
            )
            db.session.add(doctor)
            db.session.commit()

            flash("Doctor added successfully")
            return redirect(url_for('admin_doctors'))
        return render_template("admin_add_doctor.html",departments=departments)
    @app.route('/admin/doctors/edit/<int:id>',methods=['GET','POST'])
    def admin_edit_doctor(id):
        if session.get('role') !='admin':
            return redirect(url_for('login'))
        
        doctor=Doctor.query.get_or_404(id)
        departments=Department.query.all()

        if request.method =='POST':
            doctor.full_name=request.form['full_name'].strip()
            doctor.phone=request.form.get('phone', '').strip() or None
            dept_id=request.form.get('department')
            doctor.department_id=int(dept_id) if dept_id else None
            doctor.is_active=bool(request.form.get('is_active') == 'on')

            db.session.commit()
            flash("Doctor updated successfully.")
            return redirect(url_for('admin_doctors'))
        return render_template(
            'admin_edit_doctor.html',
            doctor=doctor,
            departments=departments
        )
    @app.route('/admin/doctors/toggle/<int:id>')
    def admin_toggle_doctor(id):
        if session.get('role') !='admin':
            return redirect(url_for('login'))
        
        doctor=Doctor.query.get_or_404(id)
        doctor.is_active = not doctor.is_active
        db.session.commit()

        flash("Doctor status updated.")
        return redirect(url_for('admin_doctors'))
    @app.route('/create_departments')
    def create_departments():
        from models import Department, db
        default_departments = [
            ("Cardiology", "Heart -specialist"),
            ("Neurology","Brain and nerves"),
            ("Dermatology", "Skin specialist"),
            ("General Medicines", "General medical care"),
        ]
        for name,desc in default_departments:
            existing = Department.query.filter_by(name=name).first()
            if not existing:
                dept = Department(name=name,description=desc)
                db.session.add(dept)
        db.session.commit()
        return "Departments created successfully!"
    
    @app.route('/logout')
    def logout():
        session.clear()
        flash("Logout out successfully.")
        return redirect(url_for('login'))
    @app.route('/admin/appointments')
    def admin_appointments():
        if session.get('role') != 'admin':
            return redirect(url_for('login'))
        view = request.args.get('view','upcoming')
        query=Appointment.query.join(Patient).join(Doctor)
        today=date.today()

       
        if view =='upcoming':
            query=query.filter(Appointment.date >= today).order_by(Appointment.date,Appointment.time)
        elif view == 'past':
            query=query.filter(Appointment.date < today).order_by(Appointment.date.desc(),Appointment.time.desc())
        else:
            query=query.order_by(Appointment.date.desc(),Appointment.time.desc())
        appointments = query.all()
        return render_template(
            'admin_appointments.html',
            appointments=appointments,
            view=view
        )
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if session.get('role') != "admin":
            return redirect(url_for('login'))
        total_doctors=Doctor.query.count()
        total_patients=Patient.query.count()
        total_appointments=Appointment.query.count()

        upcoming_appointments=(
            Appointment.query
            .filter(Appointment.date >= date.today())
            .order_by(Appointment.date,Appointment.time)
            .limit(10)
            .all()
        )
        return render_template(
            'admin_dashboard.html',
            total_doctors=total_doctors,
            total_patients=total_patients,
            total_appointments=total_appointments,
            upcoming_appointments=upcoming_appointments
            )
    
    @app.route('/admin/doctors')
    def admin_doctors():
        if session.get('role')!="admin":
            return redirect(url_for('login'))
        
        search = request.args.get('search','').strip()

        query=Doctor.query.outerjoin(Department)
        
        if search:
            like_pattern = f"%{search}%"
            query = query.filter(
                or_(
                Doctor.full_name.ilike(like_pattern),
                Department.name.ilike(like_pattern)
            )
            )
        doctors=query.order_by(Doctor.id).all()
        departments = Department.query.order_by(Department.name).all()

        return render_template(
            'admin_doctors.html',
            doctors=doctors,
            departments=departments,
            search=search
        )
    @app.route('/doctor/dashboard')
    def doctor_dashboard():
        if session.get('role') != "doctor":
            return redirect(url_for('login'))
        return render_template('doctor_dashboard.html')
    
    @app.route('/patient/dashboard')
    def patient_dashboard():
        if session.get('role') !='patient':
            return redirect(url_for('login'))
        return render_template('patient_dashboard.html')
    

    @app.route('/admin/patients')
    def admin_patients():
        if session.get('role') !="admin":
            return redirect(url_for('login'))
        search = request.args.get('search', '').strip()

        query = Patient.query

        if search:
            like_pattern = f"%{search}%"
            query=query.filter(
                or_(
                    Patient.full_name.ilike(like_pattern),
                    Patient.phone.ilike(like_pattern),
                    Patient.id.like(search)
                )
            )
        patients = query.order_by(Patient.id).all()

        return render_template(
            "admin_patients.html",
            patients=patients,
            search=search
        )

    return app


def ensure_default_admin():
    admin=User.query.filter_by(role="admin").first()
    if admin:
        print("Default admin already exists.")
        return
    admin_user=User(
        username="admin",
        password=generate_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.session.add(admin_user)
    db.session.commit()
    print("Created default admin -> username: admin,password: admin123")
app=create_app()

if __name__=="__main__":
    app.run(debug=True)