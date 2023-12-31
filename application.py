# -*- coding: UTF-8 -*-
from flask import Flask, redirect, url_for
from flask.cli import AppGroup
import click
from pathlib import Path

from app.flask_adminlte import AdminLTE

from app.blueprints import all_blueprints
from app.resources.views import api_bp
from importlib import import_module

from app.extensions import login_manager
from app.extensions import db
from app.extensions import bcrypt
from app.extensions import migrate

from app.user.models import User, UserRole
from flask_mail import Mail, Message
from config import config
import os


def create_app():
    flask_app = Flask(__name__, instance_relative_config=True)
    flask_app.config.update(
    DEBUG = True,
    MAIL_SERVER='smtp.163.com',
    MAIL_PROT=465,#?
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'getuplate_crypt@163.com',
    MAIL_PASSWORD = 'HIVNPIUMZXXFWMUG',
    MAIL_DEBUG = True
    )
    AdminLTE(flask_app)

    config_name = os.getenv('FLASK_CONFIG', 'default')
    flask_app.config.from_object(config[config_name])
    flask_app.config.from_pyfile('app.cfg', silent=True)

    upload_path = Path(flask_app.instance_path) / 'upload'
    if not Path(flask_app.instance_path).exists():
        Path(flask_app.instance_path).mkdir()
    if not upload_path.exists():
        upload_path.mkdir()

    flask_app.config['UPLOAD_FOLDER'] = str(upload_path)

    login_manager.session_protection = 'AdminPassword4Me'
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Unauthorized User.'
    login_manager.login_message_category = "info"

    login_manager.init_app(flask_app)
    db.init_app(flask_app)
    bcrypt.init_app(flask_app)
    migrate.init_app(flask_app, db)

    for bp in all_blueprints:
        import_module(bp.import_name)
        flask_app.register_blueprint(bp)
    flask_app.register_blueprint(api_bp)

    user_cli = AppGroup('user')

    @user_cli.command('create-admin')
    @click.argument('email')
    @click.argument('name')
    @click.argument('password')
    def create_admin(email, name, password):
        user = User(email=email,
                    email_confirmed=True,
                    name=name,
                    role=UserRole.ADMIN)
        user.password = password

        db.session.add(user)
        db.session.commit()

    flask_app.cli.add_command(user_cli)
    # 初始化 Flask-Mail
    mail = Mail(flask_app)

    # 添加 Flask-Mail 作为扩展到 Flask 应用中
    flask_app.extensions['mail'] = mail

    return flask_app


flask_app = create_app()

