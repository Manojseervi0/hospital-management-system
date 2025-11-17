import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH=Path("instance") / "db.sqlite"
ADMIN_NAME="Admin User"
ADMIN_EMAIL="admin@hospital.local"
ADMIN_PASSWORD="ADMIN_PASSWORD_REDACTED"

def create_instance():
    instance_dir=DB_PATH.parent
    if not instance_dir.exists():
        instance_dir.mkdir(parents=True)
        print(f"Created instance directory at {instance_dir}")
    else:
        print(f"Instance directory already exists at {instance_dir}")
def connect_db():
    connection=sqlite3.connect(DB_PATH)
    print(f"Connected to database at {DB_PATH}")
    return connection
def initialize_db(conn):
    cur=conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'doctor','patient')),
        contact TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
""")
    #DEPARTMENTS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
                 );
""")
    #DOCTOR TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        department_id INTEGER,
        specialization TEXT,
        base_start_time TEXT,
        base_end_time TEXT,
        slot_interval INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
        );
""")
    #patient TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        dob DATE,
        gender TEXT,
        address TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
                 );
                """)
    #materialized doctor slots
    cur.execute("""
    CREATE TABLE IF NOT EXISTS doctor_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                slot_date TEXT NOT NULL,
                slot_time TEXT NOT NULL,
                is_booked INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(doctor_id, slot_date, slot_time),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
                );
                """)
    #appointments TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        slot_date TEXT NOT NULL,
        slot_time TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('booked', 'completed', 'canceled')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id),
        UNIQUE(doctor_id, slot_date, slot_time)
                       );
                """)
    #TREATMENTS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER UNIQUE,
        diagnosis TEXT,
        prescription TEXT,
        notes TEXT,
        doctor_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
                 );
                """)
    conn.commit()
    print("Database tables created.")
if __name__=="__main__":
    create_instance()
    conn=connect_db()
    try:
        initialize_db(conn)
    finally:
        conn.close()
        print("Database connection closed.")