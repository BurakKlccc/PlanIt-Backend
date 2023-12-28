from flask_login import UserMixin
from .extensions import db,bcrypt
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime



class User(db.Model, UserMixin):
    __tablename__="users"
    id=db.Column(db.String(),primary_key=True)
    username = db.Column(db.String(length=30),nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=256), nullable=False)
    events = db.relationship('Event', backref='owned_user', lazy=True)

class Event(db.Model):
    __tablename__="events"
    id = db.Column(db.String(), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    owner = db.Column(db.String(), db.ForeignKey('users.id'),nullable=True)
    file_paths = db.relationship('FilePath', backref='event', lazy=True)
    
class FilePath(db.Model):
    __tablename__ = "file_paths"
    id = db.Column(db.String(), primary_key=True)
    path = db.Column(db.String(), nullable=False, unique=True)
    event_id = db.Column(db.String(), db.ForeignKey('events.id'), nullable=False)
    
class Session(db.Model):
    __tablename__="sessions"
    user_id = db.Column(db.String(), db.ForeignKey('users.id'),primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

@property
def is_active(self):
    return datetime.utcnow() < self.expires_at
