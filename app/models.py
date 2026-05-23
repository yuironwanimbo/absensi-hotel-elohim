from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    nama          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    foto_wajah    = db.Column(db.String(200))
    role          = db.Column(db.String(20), default='karyawan')
    aktif         = db.Column(db.Boolean, default=True)
    pin           = db.Column(db.String(10))
    jadwal_masuk  = db.Column(db.String(10))
    jadwal_pulang = db.Column(db.String(10))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    absensis = db.relationship('Absensi', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Absensi(db.Model):
    __tablename__ = 'absensi'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tanggal     = db.Column(db.Date, default=datetime.utcnow().date)
    jam_masuk   = db.Column(db.Time)
    jam_pulang  = db.Column(db.Time)
    latitude    = db.Column(db.Float)
    longitude   = db.Column(db.Float)
    foto_masuk  = db.Column(db.String(200))
    foto_pulang = db.Column(db.String(200))
    status      = db.Column(db.String(20), default='hadir')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class Pengaturan(db.Model):
    __tablename__ = 'pengaturan'
    id            = db.Column(db.Integer, primary_key=True)
    nama_hotel    = db.Column(db.String(100), default='Elohim Hotel')
    jam_masuk     = db.Column(db.String(10), default='08:00')
    jam_pulang    = db.Column(db.String(10), default='17:00')
    hotel_lat     = db.Column(db.Float, default=-2.576)
    hotel_lng     = db.Column(db.Float, default=140.516)
    radius_meters = db.Column(db.Integer, default=100)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserCredential(db.Model):
    __tablename__ = 'user_credentials'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    plain_pass  = db.Column(db.String(100))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('credential', uselist=False))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
