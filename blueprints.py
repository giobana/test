# -*- coding: UTF-8 -*-
from flask import Blueprint

home = Blueprint('home', 'app.public.views', url_prefix='/')

auth = Blueprint('auth', 'app.auth.views', url_prefix='/auth')

forgot = Blueprint('forgot', 'app.forgot.views', url_prefix='/forgot')

file = Blueprint('file', 'app.file.views', url_prefix='/file')


all_blueprints = (
    home,
    auth,
    forgot,
    file,

)
