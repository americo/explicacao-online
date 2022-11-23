import os, time
from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, Lesson, Request, Subscription, Payment
from app import db

from datetime import datetime

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg'}

def get_days_difference(timestamp):
    current_timestamp = time.time()
    timestamp = current_timestamp - float(timestamp)
    dateandtime = str(datetime.fromtimestamp(timestamp))
    dia = dateandtime.split("-")[2].split(" ")[0]
    return int(dia)

@main.route('/')
def index():
    return render_template("index.html")

@main.route('/account/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/account/profile/edit', methods=['POST'])
@login_required
def profile_edit():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')

    user = User.query.filter_by(id=current_user.id).first()
        
    user.name = name
    user.email = email
    user.phone = phone
    user.address = address
    db.session.commit()

    return redirect(url_for('main.profile'))

@main.route('/account/security')
@login_required
def security():
    return render_template('security.html')

@main.route('/account/security/edit', methods=['POST'])
@login_required
def security_edit():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    user = User.query.filter_by(id=current_user.id).first()
    if not check_password_hash(user.password, current_password):
        flash("Incorrent current password!")
        return render_template('login.html', login_failed=True)   

    if new_password != confirm_new_password:
         return render_template('profile.html', change_password_failed=True)
    
    user.password = generate_password_hash(new_password, method='sha256')
    db.session.commit()

    return redirect(url_for('main.security'))

@main.route('/delete-account', methods=['GET'])
@login_required
def delete_account():
    user = User.query.filter_by(id=current_user.id).first()

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('auth.register'))

@main.route('/lessons')
@login_required
def lessons():
    lessons = Lesson.query.all()
    users = User.query.all()
    return render_template('lessons.html', lessons=lessons, users=users)

@main.route('/my-lessons')
@login_required
def my_lessons():
    subscriptions = Subscription.query.filter_by(student_id=current_user.id).all()
    for subscription in subscriptions:
        days_diference = get_days_difference(subscription.created_at)
        if days_diference > 31:
            flash(f"A subscrição {subscription.id} expirou!")
            db.session.delete(subscription)

    db.session.commit()

    subscriptions = Subscription.query.filter_by(student_id=current_user.id).all()

    lessons = []
    for subscription in subscriptions:
        lesson = Lesson.query.filter_by(id=subscription.lesson_id).first()
        lessons.append(lesson)
    
    users = User.query.all()
    return render_template('lessons.html', lessons=lessons, users=users, subscriptions=subscriptions)


@main.route('/manage-lessons')
def manage_lessons():
    lessons = Lesson.query.filter_by(teacher_id=current_user.id).all()
    requests = Request.query.all()
    subscriptions = Subscription.query.all()
    users = User.query.all()

    return render_template('manage-lessons.html', lessons=lessons, requests=requests, subscriptions=subscriptions, users=users)

@main.route('/lesson')
@login_required
def view_lesson():
    if request.method == 'GET':
        lesson_id = request.args.get('id', '')
        lesson = Lesson.query.filter_by(id=lesson_id).first()
    elif request.method == 'POST':
        lesson_id = request.form.get('id')
        lesson = Lesson.query.filter_by(id=lesson_id).first()

    return render_template('lesson.html', current_lesson=lesson)

@main.route('/lesson/add', methods=['POST'])
@login_required
def add_lesson_post():
    subject = request.form.get('subject')
    theme = request.form.get('theme')
    schedule = request.form.get('schedule')
    zoom_link = request.form.get('zoom_link')
    price = request.form.get('price')
    teacher_id = current_user.id
    current_time = time.time()

    new_lesson = Lesson(created_at=current_time, subject=subject, theme=theme, schedule=schedule, zoom_link=zoom_link, price=price, teacher_id=teacher_id)
    
    db.session.add(new_lesson)
    db.session.commit()

    return redirect(url_for('main.manage_lessons'))

@main.route('/lesson/edit', methods=['POST'])
@login_required
def edit_lesson():
    lesson_id = request.form.get('lesson_id')
    subject = request.form.get('subject')
    theme = request.form.get('theme')
    schedule = request.form.get('schedule')
    zoom_link = request.form.get('zoom_link')
    price = request.form.get('price')
    teacher_id = current_user.id
    
    lesson = Lesson.query.filter_by(id=lesson_id).first()

    if lesson.teacher_id != teacher_id:
        flash("Você só pode editar a sua própria explicação.")
        return redirect(url_for('main.manage_lessons'))
    
    lesson.subject = subject
    lesson.theme = theme
    lesson.schedule = schedule
    lesson.zoom_link = zoom_link
    lesson.price = price
    db.session.commit()

    subscriptions = Subscription.query.filter_by(lesson_id=lesson.id).all()
    for subscription in subscriptions:
        db.session.delete(subscription)

    requests = Request.query.filter_by(lesson_id=lesson.id).all()
    for req in requests:
        db.session.delete(req)


    db.session.commit()

    return redirect(url_for('main.manage_lessons'))

@main.route('/lesson/delete', methods=['GET', 'POST'])
@login_required
def delete_lesson():
    if request.method == 'GET':
        lesson_id = request.args.get('lesson_id', '')
    elif request.method == 'POST':
        lesson_id = request.form.get('lesson_id')
    
    lesson = Lesson.query.filter_by(id=lesson_id).first()

    if lesson.teacher_id != current_user.id:
        flash("Você só pode apagar sua própria explicação.")
        return redirect(url_for('main.manage_lessons'))

    if lesson:
        db.session.delete(lesson)
        db.session.commit()

    db.session.commit()

    return redirect(url_for('main.lessons'))

@main.route('/lesson/request/add', methods=['GET', 'POST'])
@login_required
def request_lesson():
    if request.method == 'GET':
        lesson_id = request.args.get('lesson_id', '')
    elif request.method == 'POST':
        lesson_id = request.form.get('lesson_id')
    
    student_id = current_user.id
    current_time = time.time()

    requests = Request.query.filter_by(student_id=student_id).all()

    for req in requests:
        if req.lesson_id == lesson_id:            
            flash("Opa, Você já requisitou esta explicação! tente uma outra.")
            return redirect(url_for('main.lessons'))

    new_request = Request(created_at=current_time, lesson_id=lesson_id, student_id=student_id)

    db.session.add(new_request)
    db.session.commit()

    return redirect(url_for('main.manage_requests'))

@main.route('/manage-requests')
def manage_requests():
    # lessons = Lesson.query.filter_by(teacher_id=current_user.id).all()
    requests = Request.query.filter_by(student_id=current_user.id).all()
    lessons = Lesson.query.all()
    teachers = User.query.filter_by(isTeacher=True).all()

    return render_template('manage-requests.html', lessons=lessons, requests=requests, teachers=teachers)

@main.route('/request/delete', methods=['GET', 'POST'])
@login_required
def delete_request():
    if request.method == 'GET':
        request_id = request.args.get('request_id', '')
    elif request.method == 'POST':
        request_id = request.form.get('request_id')

    req = Request.query.filter_by(id=request_id).first()

    if req.student_id != current_user.id:
        flash("Você só pode cancelar sua própria requisição.")
        return redirect(url_for('main.manage_requests'))

    if req:
        db.session.delete(req)
        db.session.commit()

    db.session.commit()

    return redirect(url_for('main.manage_requests'))

@main.route('/lesson/subscription/add', methods=['POST', 'GET'])
@login_required
def add_lesson_subscription():
    if request.method == 'GET':
        request_id = request.args.get('request_id', '')
    elif request.method == 'POST':
        request_id = request.form.get('request_id')

    current_time = time.time()

    req = Request.query.filter_by(id=request_id).first()

    if current_user.isTeacher != True:
        flash("Somente explicadores podem realizar essa acção.")
        return redirect(url_for('main.lessons'))
    
    lesson = Lesson.query.filter_by(id=req.lesson_id).first()
    if current_user.id != lesson.teacher_id:
        flash("Você só pode aprovar requisições da sua própria explicação")
        return redirect(url_for('main.manage_lessons'))

    new_subscription = Subscription(created_at=current_time, student_id=req.student_id, lesson_id=req.lesson_id)
    db.session.add(new_subscription)

    db.session.delete(req)

    db.session.commit()

    return redirect(url_for('main.manage_lessons'))

@main.route('/lesson/subscription/delete', methods=['POST', 'GET'])
@login_required
def delete_lesson_subscription():
    if request.method == 'GET':
        subscription_id = request.args.get('subscription_id', '')
    elif request.method == 'POST':
        subscription_id = request.form.get('subscription_id')

    subscription = Subscription.query.filter_by(id=subscription_id).first()
    lesson = Lesson.query.filter_by(id=subscription.lesson_id).first()

    if current_user.id != lesson.teacher_id:
        if subscription.student_id != current_user.id:
                flash("Você só pode cancelar sua própria subscrição.")
                return redirect(url_for('main.manage_requests'))

    if subscription:
        db.session.delete(subscription)
        db.session.commit()

    db.session.commit()

    if current_user.isTeacher == True:
        return redirect(url_for('main.manage_lessons'))
    else:
        return redirect(url_for('main.my_lessons'))

@main.route('/payments')
@login_required
def payments():
    if current_user.isTeacher == True:
        payments = Payment.query.filter_by(teacher_id=current_user.id)
    else:
        payments = Payment.query.filter_by(student_id=current_user.id)

    students = User.query.filter_by(isTeacher=False).all()
    teachers = User.query.filter_by(isTeacher=True).all()

    total_price = 0

    for payment in payments:
        total_price += payment.amount

    return render_template("payments.html", payments=payments, students=students, teachers=teachers, total_price=total_price)

@main.route('/payment/paypal/success', methods=['POST', 'GET'])
@login_required
def success_paypal_payment():
    if request.method == 'GET':
        request_id = request.args.get('request_id', '')
        amount = request.args.get('amount', '')
    elif request.method == 'POST':
        request_id = request.form.get('request_id')
        amount = request.args.get('amount', '')
    
    current_time = time.time()

    req = Request.query.filter_by(id=request_id).first()
    lesson = Lesson.query.filter_by(id=req.lesson_id).first()

    new_subscription = Subscription(created_at=current_time, student_id=req.student_id, lesson_id=req.lesson_id)
    new_payment = Payment(created_at=current_time, student_id=req.student_id, teacher_id=lesson.teacher_id, amount=amount)

    if int(amount) < lesson.price:
        flash("Quantia de pagamento insuficiente, tente novamente!")
        return redirect(url_for('main.manage_requests'))
    
    db.session.add(new_subscription)
    db.session.add(new_payment)
    db.session.delete(req)
    db.session.commit()
    
    flash("Pagamento realizado com êxito, você está inscrito!")
    return redirect(url_for('main.my_lessons'))

@main.route('/payment/paypal/failed', methods=['POST', 'GET'])
@login_required
def failed_paypal_payment():
    flash("Pagamento falhou, tente novamente!")
    return redirect(url_for('main.manage_requests'))

@main.route('/payment/withdraw', methods=['POST', 'GET'])
@login_required
def withdraw_payment():
    if current_user.isTeacher == False:
        flash("Apenas explicadores podem transferir fundos!")

    payments = Payment.query.filter_by(teacher_id=current_user.id).all()

    for payment in payments:
        db.session.delete(payment)

    db.session.commit()
    
    flash("Transferência concluída com êxito!")
    return redirect(url_for('main.payments'))

@main.route('/watch', methods=['GET'])
@login_required
def watch():
    zoom_url = request.form.get('zoom_url', '')
    return render_template("watch.html", zoom_url=zoom_url)


@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))