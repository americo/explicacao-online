
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.String(1000))
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(100), unique=True)
    address = db.Column(db.String(1000))
    password = db.Column(db.String(100))
    isTeacher = db.Column(db.Boolean)

class Lesson(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.String(1000))
    subject = db.Column(db.String(1000))
    theme = db.Column(db.String(1000))
    schedule = db.Column(db.String(1000))
    zoom_link = db.Column(db.String(1000))
    price = db.Column(db.Integer)
    teacher_id = db.Column(db.Integer)

class Request(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.String(1000))
    student_id = db.Column(db.Integer)
    lesson_id = db.Column(db.Integer)

class Subscription(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.String(1000))
    student_id = db.Column(db.Integer)
    lesson_id = db.Column(db.Integer)

class Payment(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.String(1000))
    student_id = db.Column(db.Integer)
    teacher_id = db.Column(db.Integer)
    amount = db.Column(db.Integer)