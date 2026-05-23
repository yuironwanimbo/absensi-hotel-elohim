from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, UserCredential
from app.auth.forms import LoginForm

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Email atau password salah', 'danger')
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not nama or not email or not password:
            flash('Semua field wajib diisi', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email sudah terdaftar', 'danger')
        else:
            u = User(nama=nama, email=email, role='karyawan')
            u.set_password(password)
            db.session.add(u)
            db.session.flush()
            cred = UserCredential(user_id=u.id, plain_pass=password)
            db.session.add(cred)
            db.session.commit()
            flash(f'Pendaftaran berhasil! Email: {email}, Password: {password}', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))