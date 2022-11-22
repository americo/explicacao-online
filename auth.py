from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from flask_login import login_user, logout_user, current_user

from app import db

import binascii
import os, time

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return render_template('login.html', login_failed=True)    
     
    login_user(user, remember=remember)

    return redirect(url_for('main.lessons'))
    
@auth.route('/register')
def register():
    return render_template('register.html')

@auth.route('/register', methods=['POST'])    
def register_post():
    email = request.form.get('email')
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    password = request.form.get('password')
    type = request.form.get("type")
    current_time = time.time()

    if type == "Estudante":
        isTeacher = False
    elif type == "Explicador":
        isTeacher = True
    
    user = User.query.filter_by(email=email).first()
    if user:
            flash('Email address already exists')
            return redirect(url_for('auth.register'))

    user = User(created_at=current_time, email=email, name=name, phone=phone, address=address, password=generate_password_hash(password, method='sha256'), isTeacher=isTeacher)

    db.session.add(user)
    db.session.commit()

    return redirect(url_for('auth.login'))