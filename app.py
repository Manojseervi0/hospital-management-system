from flask import Flask , render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import or_ 
from config import Config
from datetime import date,time,datetime,timedelta
from models import db,User,Patient,Doctor,Appointment,Department,Treatment,DoctorAvailability

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
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if not doctor:
            flash("Doctor profile not found. Please contact admin.")
            return redirect(url_for('logout'))
        
        today=date.today()

        total_appointments = Appointment.query.filter_by(
            doctor_id=doctor.id
        ).count()

        pending_count = Appointment.query.filter(
            Appointment.doctor_id==doctor.id,
            Appointment.status=="Booked"
        ).count()

        completed_count = Appointment.query.filter(
            Appointment.doctor_id==doctor.id,
            Appointment.status=="Completed"
        ).count()

        today_appointments = (
            Appointment.query
            .join(Patient,Appointment.patient_id==Patient.id)
            .filter(
                Appointment.doctor_id==doctor.id,
                Appointment.date==today
            )
            .order_by(Appointment.time)
            .all()
        )
        return render_template(
            'doctor_dashboard.html',
            doctor=doctor,
            total_appointments=total_appointments,
            pending_count=pending_count,
            completed_count=completed_count,
            today_appointments=today_appointments,
            today=today
            )
    
    @app.route('/patient/dashboard')
    def patient_dashboard():
        if session.get('role') !='patient':
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        patient = Patient.query.filter_by(user_id=user_id).first()
        if not patient:
            flash("Patient profile not found.")
            return redirect(url_for('logout'))
        
        today=date.today()

        upcoming_appointments =(
            Appointment.query
            .filter(
                Appointment.patient_id == patient.id,
                Appointment.date >=today,
                
            )
            .order_by(Appointment.date,Appointment.time)
            .all()
        )
        past_appointments =(
            Appointment.query
           .filter(
                Appointment.patient_id==patient.id,
                Appointment.date < today,
        
            )
            .order_by(Appointment.date.desc(),Appointment.time.desc()).all()
        )

        departments = Department.query.order_by(Department.name).all()
        return render_template(
            'patient_dashboard.html',
            patient=patient,
            departments=departments,
            upcoming_appointments=upcoming_appointments,
            past_appointments=past_appointments,
            
            )
    
    @app.route('/patient/doctors')
    def patient_search_doctors():
        if session.get('role') != 'patient':
            return redirect(url_for('login'))
        
        dept_id=request.args.get('dept_id', type=int)
        search = request.args.get('search', '').strip()

        query = (
            Doctor.query
            .join(Department, Doctor.department_id==Department.id)
            .filter(Doctor.is_active==True)
        )
        if dept_id:
            query = query.filter(Doctor.department_id==dept_id)

        if search:
            like=f"%{search}%"
            query=query.filter(
                or_(
                    Doctor.full_name.ilike(like),
                    Department.name.ilike(like)
                )
            )
        doctors = query.filter(Doctor.is_active == True).order_by(Doctor.full_name).all()
        departments = Department.query.order_by(Department.name).all()
        return render_template(
            'patient_doctors.html',
            doctors=doctors,
            departments=departments,
            selected_dept_id=dept_id,
            search=search
            )
    
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

    @app.route('/admin/patients/toggle/<int:patient_id>')
    def admin_toggle_patient(patient_id):
        if session.get('role') !="admin":
            return redirect(url_for('login'))
        
        patient = Patient.query.get_or_404(patient_id)
        user=User.query.get_or_404(patient.user_id)

        user.is_active=not user.is_active
        db.session.commit()

        flash(
            f"Patient '{patient.full_name}' has been"
            + ("activated." if user.is_active else "deactivated.")
        )
        return redirect(url_for('admin_patients'))

    @app.route('/admin/patient/<int:patient_id>/history')
    def admin_patient_history(patient_id):
        if session.get('role') !="admin":
            return redirect(url_for('login'))
        
        patient=Patient.query.get_or_404(patient_id)

        appointments=(
            Appointment.query
            .filter_by(patient_id=patient.id)
            .order_by(Appointment.date.desc(),Appointment.time.desc())
            .all()
        )
        return render_template(
            "admin_patient_history.html",
            patient=patient,
            appointments=appointments,
        )

    @app.route('/admin/appointments/<int:appt_id>')
    def admin_appointment_detail(appt_id):
        if session.get('role') !='admin':
            return redirect(url_for('login'))
        
        appt = Appointment.query.get_or_404(appt_id)
        return render_template("Admin_appointment_detail.html",appointment=appt)

    @app.route('/doctor/appointments')
    def doctor_appointments():
        if session.get('role') != "doctor":
            return redirect(url_for('login'))
        
        user_id=session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if not doctor:
            flash("Doctor profile not found. Please contact admin.")
            return redirect(url_for('logout'))
        
        view = request.args.get('view','today')
        today=date.today()

        query = (
            Appointment.query
            .join(Patient, Appointment.patient_id==Patient.id)
            .filter(Appointment.doctor_id == doctor.id)
        )
        if view =="today":
            query=query.filter(Appointment.date == today).order_by(Appointment.time)
        elif view == "upcoming":
            query = query.filter(Appointment.date > today).order_by(Appointment.date,Appointment.time)
        elif view =="past":
            query = query.filter(Appointment.date < today).order_by(Appointment.date.desc(), Appointment.time.desc())
        else:
            query = query.order_by(Appointment.date.desc(),Appointment.time.desc())

        appointments = query.all()

        return render_template(
            "doctor_appointments.html",
            doctor=doctor,
            appointments=appointments,
            view=view,
            today=today
        )                
    
    @app.route('/doctor/appointments/<int:id>/status/<string:new_status>')
    def doctor_update_status(id, new_status):
        if session.get('role') !='doctor':
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if not doctor:
            flash("Doctor profile not found.")
            return redirect(url_for('doctor_dashboard'))
        
        appointment=Appointment.query.get_or_404(id)

        if appointment.doctor_id != doctor.id:
            flash("You cannot modify another doctor's appointment.")
            return redirect(url_for('doctor_appointments'))
        
        valid = ["Completed","Cancelled"]
        if new_status not in valid:
            flash("Invalid status.")
            return redirect(url_for('doctor_apppointments'))
        
        appointment.status = new_status
        db.session.commit()

        flash(f"Appointment marked as {new_status}.")
        return redirect(url_for('doctor_appointments'))
    
    @app.route('/doctor/patient/history/<int:patient_id>/history')
    def doctor_patient_history(patient_id):
        if session.get('role') != "doctor":
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if not doctor:
            flash("Doctor profile not found.")
            return redirect(url_for('doctor_dashboard'))
        
        patient=Patient.query.get_or_404(patient_id)

        appointments = (
            Appointment.query
            .filter_by(patient_id=patient.id,doctor_id=doctor.id)
            .order_by(Appointment.date.desc(),Appointment.time.desc())
            .all()
        )
        return render_template(
            "doctor_patient_history.html",
            patient=patient,
            appointments=appointments,
        )

    @app.route('/patient/doctor/<int:doctor_id>')
    def patient_doctor_profile(doctor_id):
        if session.get('role') != "patient":
            return redirect(url_for('login'))
        
        doctor = Doctor.query.get_or_404(doctor_id)

        today=date.today()
        next_week = today + timedelta(days=7)
        slots = (
            DoctorAvailability.query
            .filter(
                DoctorAvailability.doctorid==doctor.id,
                DoctorAvailability.date>=today,
                DoctorAvailability.date <= next_week
            ).order_by(DoctorAvailability.date,DoctorAvailability.start_time).all()
        )
        return render_template(
            "patient_doctor_profile.html",
            doctor=doctor,
            slots=slots
        )
    
    @app.route('/patient/book/<int:slot_id>', methods=['POST'])
    def patient_book_appointment(slot_id):
        if session.get('role')!="patient":
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        patient=Patient.query.filter_by(user_id=user_id).first()
        if not patient:
            flash("Patient profile not found.")
            return redirect(url_for('logout'))
        
        slot = DoctorAvailability.query.get_or_404(slot_id)

        existing_for_doctor = Appointment.query.filter(
            Appointment.doctor_id ==slot.doctorid,
            Appointment.date ==slot.date,
            Appointment.time == slot.start_time,
            Appointment.status != "Cancelled"
        ).first()

        if existing_for_doctor:
            flash("this slot has already been booked by another patient.")
            return redirect(url_for('patient_dashboard'))
        

        
        existing_for_patient = Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.doctor_id==slot.doctorid,
            Appointment.date==slot.date,
            Appointment.time==slot.start_time,
            Appointment.status != "Cancelled"
            ).first()
        if existing_for_patient:
            flash("You already have an appointment in this time slot.")
            return redirect(url_for('patient_dashboard'))
        
        appt = Appointment(
            patient_id=patient.id,
            doctor_id=slot.doctorid,
            date=slot.date,
            time=slot.start_time,
            status="Booked",
        )
        db.session.add(appt)
        db.session.commit()

        flash("Appointment booked successfully.")
        return redirect(url_for('patient_dashboard'))

    @app.route('/patient/appointment/cancel/<int:appt_id>',methods=['POST'])
    def patient_cancel_appointment(appt_id):
        if session.get('role') !='patient':
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        patient = Patient.query.filter_by(user_id=user_id).first()
        if not patient:
            flash("Patient profile not found.")
            return redirect(url_for('logout'))

        appointment = Appointment.query.get_or_404(appt_id)
        if appointment.patient_id !=patient.id:
            flash("You cannot cancel another patient's appointment.")
            return redirect(url_for('patient_dashboard'))
        today=date.today()
        if appointment.date < today or appointment.status != "Booked":
            flash("Only booked appointments can be cancelled.")
            return redirect(url_for('patient_dashboard'))
        
        appointment.status = "Cancelled"
        db.session.commit()

        flash("Appointment cancelled successfully.")
        return redirect(url_for('patient_dashboard'))

    @app.route('/patient/appointment/reschedule/<int:appt_id>')
    def patient_reschedule_appointment(appt_id):
        if session.get('role') !='patient':
            return redirect(url_for('login'))
        
        user_id=session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        patient=Patient.query.filter_by(user_id=user_id).first()
        if not patient:
            flash("Patient profile not found.")
            return redirect(url_for('logout'))
        
        appt=Appointment.query.get_or_404(appt_id)

        if appt.patient_id != patient.id or appt.status !="Booked":
            flash("You can only reschedule your own booked appointments.")
            return redirect(url_for('patient_dashboard'))
        
        today = date.today()
        slots = (
            DoctorAvailability.query
            .filter(
                DoctorAvailability.doctorid==appt.doctor_id,
                DoctorAvailability.date>=today,
                DoctorAvailability.date<=today +timedelta(days=7),
            )
            .order_by(DoctorAvailability.date,DoctorAvailability.start_time).all()
        )
        return render_template(
            "patient_reschedule.html",
            appointment=appt,
            slots=slots
        )

    @app.route('/patient/appointment/reschedule/<int:appt_id>/slot/<int:slot_id>', methods=['POST'])
    def patient_apply_reschedule(appt_id,slot_id):
        if session.get('role') !='patient':
            return redirect(url_for('login'))
        
        user_id=session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        patient=Patient.query.filter_by(user_id=user_id).first()
        if not patient:
            flash("Patient profile not found.")
            return redirect(url_for('logout'))
        
        appt=Appointment.query.get_or_404(appt_id)
        if appt.patient_id != patient.id or appt.status != "Booked":
            flash("You can only reschedule your own booked appointments.")
            return redirect(url_for('patient_dashboard'))
        
        slot=DoctorAvailability.query.get_or_404(slot_id)
        if slot.doctorid != appt.doctor_id:
            flash("Invalid slot for this doctor.")
            return redirect(url_for('patient_reschedule_appointment',appt_id=appt.id))
        appt.date=slot.date
        appt.time=slot.start_time

        db.session.commit()
        flash("Appointement rescheduled successfully.")
        return redirect(url_for('patient_dashboard'))

    @app.route('/patient/profile', methods=['GET','POST'])
    def patient_edit_profile():
        if session.get('role') !='patient':
            return redirect(url_for('login'))
        
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))
        
        patient=Patient.query.filter_by(user_id=user_id).first()
        if not patient:
            flash("Patient profile not found.")
            return redirect(url_for('logout'))
        
        if request.method=='POST':
            full_name = request.form.get('full_name','').strip()
            phone = request.form.get('phone','').strip()
            age_str = request.form.get('age','').strip()
            gender = request.form.get('gender', '').strip()

            if not full_name:
                flash("Name cannot be empty.")
                return redirect(url_for('patient_edit_profile'))
            
            patient.full_name =full_name
            patient.phone = phone or None

            if age_str.isdigit():
                patient.age=int(age_str)
            else:
                patient.age=None
            
            patient.gender= gender or None

            db.session.commit()
            flash("Profile updated successfully.")
            return redirect(url_for('patient_dashboard'))
        
        return render_template(
            'patient_edit_profile.html',patient=patient
        )

    @app.route('/doctor/availability',methods=['GET','POST'])
    def doctor_availability():
        if session.get('role') != "doctor":
            return redirect(url_for('login'))
        
        
        
        doctor = Doctor.query.filter_by(user_id=session['user_id']).first_or_404()
        

        if request.method =="POST":
            date_str = request.form.get('date', '').strip()
            start_str = request.form.get('start_time', '').strip()
            end_str= request.form.get('end_time', '').strip()

            try:
                slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                start_time=datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
            except (TypeError, ValueError):
                flash("Invalid date or time format.")
                return redirect(url_for('doctor_availability'))
            today=date.today()
            if not (today <= slot_date <= today + timedelta(days=7)):
                flash("Date must be withing the next 7 days.")
                return redirect(url_for('doctor_availability'))
            
            if end_time<=start_time:
                flash("End time must be after start time.")
                return redirect(url_for('doctor_availability'))
            
            overlapping=DoctorAvailability.query.filter(
                DoctorAvailability.doctorid ==doctor.id,
                DoctorAvailability.date==slot_date,
                DoctorAvailability.start_time <end_time,
                DoctorAvailability.end_time > start_time,
            ).first()

            if overlapping:
                flash("This time range overlaps with an existing availability slot.")
                return redirect(url_for('doctor_availability'))

            new_slot = DoctorAvailability(
                doctorid=doctor.id,
                date=slot_date,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(new_slot)
            db.session.commit()
            flash("Availability slot added.")
            return redirect(url_for('doctor_availability'))

        upcoming = (
            DoctorAvailability.query
            .filter(
                DoctorAvailability.doctorid==doctor.id,
                DoctorAvailability.date >=date.today(),
                DoctorAvailability.date <= date.today() + timedelta(days = 7),
            )
            .order_by(DoctorAvailability.date,DoctorAvailability.start_time)
            .all()
        )
            
        return render_template(
            "doctor_availability.html",
            upcoming=upcoming
        )
    
    @app.route('/doctor/availability/delete/<int:slot_id>')
    def doctor_delete_availability(slot_id):
        if session.get('role') !="doctor":
            return redirect(url_for('login'))
        user_id=session.get('user_id')
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if not doctor:
            flash("Doctor profile not found.")
            return redirect(url_for('doctor_dashboard'))
        
        slot = DoctorAvailability.query.get_or_404(slot_id)

        if slot.doctorid != doctor.id:
            flash("You cannot delete another doctor's availability.")
            return redirect(url_for('doctor_availability'))
        
        db.session.delete(slot)
        db.session.commit()
        flash("Avialability slot deleted.")
        return redirect(url_for('doctor_availability'))
    
    @app.route('/doctor/treatment/<int:appointment_id>',methods=['GET','POST'])
    def doctor_treatment(appointment_id):
        if session.get('role') != "doctor":
            return redirect(url_for('login'))
        doctor=Doctor.query.filter_by(user_id=session['user_id']).first_or_404()

        appt=(
            Appointment.query.filter_by(id=appointment_id,doctor_id=doctor.id)
            .join(Patient)
            .first_or_404()
        )

        treatment= Treatment.query.filter_by(appointment_id=appt.id).first()
        if request.method=='POST':
            diagnosis = request.form.get('diagnosis', '').strip()
            prescription = request.form.get('prescription', '').strip()
            notes = request.form.get('notes', '').strip()

            if not treatment:
                treatment=Treatment(
                    appointment_id=appt.id,
                    diagnosis=diagnosis or None,
                    prescription=prescription or None,
                    notes=notes or None,
                )
                db.session.add(treatment)
            else:
                treatment.diagnosis = diagnosis or None
                treatment.prescription = prescription or None
                treatment.notes = notes or None

            if appt.status =="Booked":
                appt.status = "Completed"
            
            db.session.commit()
            flash("Treatment details saved.")
            return redirect(url_for('doctor_treatment',appointment_id=appt.id))
        
        patient_history = (
            Appointment.query
            .filter(
                Appointment.patient_id==appt.patient_id,
                Appointment.id != appt.id,
                Appointment.status != 'Cancelled'
            )
            .order_by(Appointment.date.desc(), Appointment.time.desc())
            .all()
        )
        return render_template(
            "doctor_treatment.html",
            appointment=appt,
            treatment=treatment,
            patient_history=patient_history
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