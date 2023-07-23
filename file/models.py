# -*- coding: UTF-8 -*-
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, and_
from os import remove, path, mkdir
import re
from pathlib import *

from app.file.config import allowed_file_suffix_list
from app.extensions import db
from app.extensions import bcrypt
from app.user.models import User,UserRole

import enum
import hashlib

from flask import current_app


filename_pattern = re.compile(r'[^\u4e00-\u9fa5]+')


class File(db.Model):
    __tablename__ = 'files'
    creator_id = db.Column(db.Integer, db.ForeignKey('app.user.models.User.id', ondelete='CASCADE'), primary_key=True)
    filename = db.Column(db.String(64), primary_key=True)
    hash_value = db.Column(db.String(128))
    shared = db.Column(db.Boolean, default=False)

    @classmethod
    ## 对上传的文件做限制
    def upload_file(cls, user, data):
        from hashlib import sha512
        from app.file.config import allowed_file_suffix_list
        filename = data.filename
        filename_suffix = PurePath('filename').suffix
        assert filename_suffix in allowed_file_suffix_list, '禁止上传该类型的文件（应上传office文档，或允许的图片类型文件）' ## 文件类型限制
        f = File.query.filter(and_(File.creator_id == user.id, File.filename == filename)).first()
        assert not f, '该文件已存在'  ## 文件秒传
        content = data.read()
        assert len(content) < 10*1024*1024, '文件过大 (应小于10MB)' ## 文件大小限制
        user_id = str(user.id)+'/'
        if not path.exists(Path + user_id):
            if not path.exists(Path):
                mkdir(Path)
            mkdir(Path + user_id)
            ## 对文件进行对称加密存储到文件系统，禁止明文存储文件
        # 计算原文件的哈希
        hash_value = sha512(content).hexdigest()
        # 判断文件是否存在
        if not path.exists(Path + user_id + hash_value):
            # 加密并存储。加密前得先还原出对称密钥。
            content = secret.symmetric_encrypt(secret.decrypt(user.encrypted_symmetric_key), content)
            # 同时计算签名
            signature = secret.sign(content)
            # 保存密文与签名
            with open(Path + user_id + hash_value, 'wb') as f:
                f.write(content)
            with open(Path + user_id + hash_value+'.sig', 'wb') as f:
                f.write(signature)
        creator_id = user.id_
        file = File(creator_id=creator_id, filename=filename, hash_value=hash_value)
        db.session.add(file)
        db.session.commit()

    @classmethod
    ## 删除文件
    def delete_file(cls, user, filename):  
        f = File.query.filter(and_(File.creator_id == user.id, File.filename == filename)).first()
        assert f, 'no such file ({})'.format(filename)
        hash_value = f.hash_value
        db.session.delete(f)
        db.session.commit()
        files = File.query.filter(File.hash_value == hash_value).all()
        if not len(files):
            remove(Path + str(user.id) + '/'+hash_value)
            remove(Path + str(user.id) + '/'+hash_value+'.sig')

    @classmethod
    ## 系统对加密后文件进行数字签名 
    def download_file(cls, user, filename, type_):
        from flask import make_response
        f = File.query.filter(and_(File.creator_id == user.id, File.filename == filename)).first()
        assert f, 'no such file ({})'.format(filename)
        hash_value = f.hash_value
        if type_ == 'hashvalue':
            content = hash_value
            filename = filename + '.hash'
        elif type_ == 'signature':
            # 读取签名
            with open(Path + str(user.id) + '/' + hash_value+'.sig', 'rb') as f_:
                content = f_.read()
                filename = filename+'.sig'
        else:
            # 读取密文
            with open(Path + str(user.id)+'/' + hash_value, 'rb') as f_:
                content = f_.read()
            if type_ == 'plaintext':
                content = secret.symmetric_decrypt(secret.decrypt(user.encrypted_symmetric_key), content)
            elif type_ == 'encrypted':
                filename = filename + '.encrypted'
        response = make_response(content)
        response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        return response

    @classmethod
    def share_file(cls, user, filename):
        f = File.query.filter(and_(File.creator_id == user.id, File.filename == filename)).first()
        assert f, 'no such file ({})'.format(filename)
        f.shared = not f.shared
        db.session.commit()