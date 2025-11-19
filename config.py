import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
class Config:
    SECRET_KEY="qwerty"
    DB_PATH=os.path.join(BASE_DIR,"hospital.db")
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False