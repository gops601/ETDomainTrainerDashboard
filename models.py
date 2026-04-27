from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='trainer') # 'admin', 'domain_lead', 'trainer'
    domain = db.Column(db.String(50), nullable=True) # e.g. 'ET', 'AI', 'Cyber', 'DM'
    trainer_type = db.Column(db.String(20), nullable=True) # 'Inhouse', 'External'
    external_type = db.Column(db.String(20), nullable=True) # 'TSP', 'Empanelled'
    tsp_name = db.Column(db.String(100), nullable=True)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    
    entries = db.relationship('TrainingEntry', backref='trainer', lazy=True)

class OU(db.Model):
    __tablename__ = 'organizational_units'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    training_types = db.relationship('TrainingType', backref='ou', lazy=True, cascade='all, delete-orphan')
    entries = db.relationship('TrainingEntry', backref='ou', lazy=True)

class TrainingType(db.Model):
    __tablename__ = 'training_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ou_id = db.Column(db.Integer, db.ForeignKey('organizational_units.id'), nullable=False)
    
    entries = db.relationship('TrainingEntry', backref='training_type', lazy=True)

class TrainingEntry(db.Model):
    __tablename__ = 'training_entries'
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    is_training = db.Column(db.Boolean, default=True, nullable=False)
    ou_id = db.Column(db.Integer, db.ForeignKey('organizational_units.id'), nullable=True)
    training_type_id = db.Column(db.Integer, db.ForeignKey('training_types.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    participants_count = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Float, nullable=False, default=0.0)
    mode = db.Column(db.String(50), nullable=True) # 'Online' or 'Offline'
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
