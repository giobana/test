# -*- coding: UTF-8 -*-
from flask import render_template, redirect, url_for, request
from flask_login import LoginManager, login_required, login_user, logout_user

from app.auth.forms import SignInForm
from app.auth.forms import SignUpForm

from app.blueprints import auth
from app.user.models import User,UserRole

from app.extensions import db
from app.extensions import login_manager
import re
import hashlib
import os

from sqlalchemy.exc import IntegrityError

@login_manager.user_loader
def load_user(userid):
    return User.query.filter(User.id == userid).first()


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first_or_404()

        if user.is_correct_password(form.password.data):
            login_user(user)
            next = request.args.get('next')
            return redirect(next or url_for('home.index'))
        else:
            return redirect(url_for('auth.login'))
    return render_template('auth/login.html', form=form)

username_pattern = re.compile(r'[\u4e00-\u9fa5a-zA-Z0-9]+')
password_pattern = re.compile(r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[\s\S]{8,36}')

@auth.route('/register')
def get_register():
    return render_template('auth/register.html', form=SignUpForm())

@auth.route('/register',methods=['GET', 'POST'])
def post__register():
    try:
        form=SignUpForm()
        username=form.username.data
        if not username_pattern.fullmatch(username):
             raise AssertionError("用户名只能使用数字、中文和英文")
        email=form.email.data
        if User.query.filter_by(email=email).first():
             raise AssertionError("该email已被注册")
        password=form.password.data
        if not password_pattern.fullmatch(password):
            raise AssertionError("密码不安全,同时包含至少一个小写字母,一个大写字母和一个数字,长度8-36")
        

        user = User(email=email,
                    email_confirmed=True,
                    name=username,
                    role=UserRole.ADMIN)
        user.password = password
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('auth.login'))
    except AssertionError as e:
        message = e.args[0] if len(e.args) else str(e)
        return render_template('auth/register.html', form=SignUpForm(), message=message)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('auth/logout.html')

