from flask import Flask , render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash

from config import Config
from models import db,User

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
    @app.route('/logout')
    def logout():
        session.clear()
        flash("Logout out successfully.")
        return redirect(url_for('login'))
    
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if session.get('role') != "admin":
            return redirect(url_for('login'))
        return render_template('admin_dashboard.html')
    

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