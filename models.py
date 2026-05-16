from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()
#usermodel
class User(UserMixin,db.Model):
    #basic login info foradmin/doctors/patientss
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80), unique=True,nullable=False)
    password=db.Column(db.String(255), nullable=False)
    role=db.Column(db.String(20),nullable=False)
    is_active=db.Column(db.Boolean,default=True)
    
    patient_profile=db.relationship("Patient",back_populates="user",uselist=False)
    doctor_profile=db.relationship("Doctor",back_populates="user",uselist=False)

    def __repr__(self):
        return f"<User {self.username} role={self.role}>"
#patients
class Patient(db.Model):
    __tablename__="patients"    

    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    full_name=db.Column(db.String(120), nullable=False)
    age= db.Column(db.Integer)
    gender=db.Column(db.String(10))
    phone=db.Column(db.String(20))
    address=db.Column(db.String(255))
    is_balcklisted=db.Column(db.Boolean,default=False)

    user=db.relationship("User",back_populates="patient_profile")
    appointments=db.relationship("Appointment",back_populates="patient")

    def __repr__(self):
        return f"<Patient {self.full_name} id={self.id}>"
    
#depaartments andn doctoir

class Department(db.Model):
    __tablename__="departments"

    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(80),unique=True,nullable=False)
    description=db.Column(db.Text)

    doctors=db.relationship("Doctor",back_populates="department")
    def __repr__(self):
        return f"<Department {self.name}>"
class Doctor(db.Model):
    __tablename__="doctors"
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    department_id=db.Column(db.Integer,db.ForeignKey("departments.id"))
    full_name=db.Column(db.String(120),nullable=False)
    phone=db.Column(db.String(20))
    about=db.Column(db.Text)
    experience_years=db.Column(db.Integer)
    is_active=db.Column(db.Boolean, default=True)

    user=db.relationship("User",back_populates="doctor_profile")
    department=db.relationship("Department",back_populates="doctors")
    appointments=db.relationship("Appointment",back_populates="doctor")
    availabilities=db.relationship("DoctorAvailability",back_populates="doctor")
    def __repr__(self):
        return f"<Doctor {self.full_name} dept_id={self.department_id}>"
    

    #appointments and tereatements

class Appointment(db.Model):
    __tablename__="appointments"
    id =db.Column(db.Integer,primary_key=True)
    patient_id=db.Column(db.Integer,db.ForeignKey("patients.id"),nullable=False)
    doctor_id=db.Column(db.Integer,db.ForeignKey("doctors.id"),nullable=False)

    #store date and time 
    date=db.Column(db.Date,nullable=False)
    time=db.Column(db.Time,nullable=False)
    
    status=db.Column(db.String(20),default="Booked")

    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    updated_at=db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

    patient=db.relationship("Patient",back_populates="appointments")
    doctor=db.relationship("Doctor",back_populates="appointments")

    treatment=db.relationship("Treatment",back_populates="appointment",uselist=False)
    def __repr__(self):
        return f"<Appointment {self.id} {self.date} {self.time} status={self.status}>"

class Treatment(db.Model):
    __tablename__="treatments"

    id=db.Column(db.Integer,primary_key=True)
    appointment_id=db.Column(db.Integer,db.ForeignKey("appointments.id"), nullable=False,unique=True)
    diagnosis=db.Column(db.Text)
    prescription=db.Column(db.Text)
    notes=db.Column(db.Text)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    appointment=db.relationship("Appointment",back_populates="treatment")  
    
    def __repr__(self):
        return f"<Treatment appt_id={self.appointment_id}>"
    
class DoctorAvailability(db.Model):
    __tablename__="doctor_availability"
    id=db.Column(db.Integer,primary_key=True)
    doctorid=db.Column(db.Integer,db.ForeignKey("doctors.id"),nullable=False)
    date=db.Column(db.Date,nullable=False)
    start_time=db.Column(db.Time,nullable=False)
    end_time=db.Column(db.Time,nullable=False)

    doctor=db.relationship("Doctor",back_populates="availabilities")

    def __repr__(self):
        return f"<Avail doctor={self.doctorid} date={self.date}{self.start_time}-{self.end_time}>"
    
