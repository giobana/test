from flask import Blueprint, render_template, flash, redirect, request
from app.file.models import File
from app.user.models import User,UserRole
from app.extensions import db
from flask_login import login_required
from app.blueprints import file


## 所有用户都可以浏览文件
@file.route('/')
@login_required
def get__file(user):
    from models import File
    files = File.query.filter(File.creator_id == user.id).all()
    return render_template('file.html', username=user.id, files=files)

## 以下函数都限制只有登录用户才能调用以下函数对文件进行处理（即匿名用户不能对文件进行处理

## 提交上传文件请求
@file.route('/upload')
@login_required
def get__upload():
    from forms import FileForm
    return render_template('file/upload.html', form=FileForm()) ## 链接到上传文件页面

## 处理请求后返回处理结果
@file.route('/upload', methods=['POST'])
@login_required
def post__upload(user):
    try:
        from forms import FileForm
        form = FileForm()
        assert form.validate_on_submit(), 'invalid form fields'
        data = form.file.data
        File.upload_file(user, data)
        flash('上传成功！')
    except AssertionError as e:
        message = e.args[0] if len(e.args) else str(e)
        flash('上传失败！'+message)
    return redirect('/file')

## 删除文件
@file.route('/remove')
@login_required
def get__remove(user):
    try:
        filename = request.args.get('filename')
        assert filename, 'missing filename'
        File.delete_file(user, filename)
        flash('删除成功！')
    except AssertionError as e:
        message = e.args[0] if len(e.args) else str(e)
        flash('删除失败！'+message)
    return redirect('/file')

## 下载文件到本地
@file.route('/download')
@login_required
def get__download(user):
    try:
        filename = request.args.get('filename')
        assert filename, 'missing filename'
        type_ = request.args.get('type')
        assert type_, 'missing type'
        assert type_ in ('encrypted', 'plaintext', 'signature', 'hashvalue'), 'unknown type'
        return File.download_file(user, filename, type_)
    except AssertionError as e:
        message = e.args[0] if len(e.args) else str(e)
        flash('下载失败！'+message)
        return redirect('/file')

## 设置文件共享
@file.route('/share')
@login_required
def get__share(user):
    try:
        filename = request.args.get('filename')
        assert filename, 'missing filename'
        File.share_file(user, filename)
        flash('设置成功！')
        return redirect('/file')
    except AssertionError as e:
        message = e.args[0] if len(e.args) else str(e)
        flash('设置失败！'+message)
        return redirect('/file')