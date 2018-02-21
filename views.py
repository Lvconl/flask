#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : views.py
# @Author: lvconl
# @Date  : 18-2-10
#@Software : PyCharm
from flask import render_template,make_response,request,redirect,session

from main import app
from models import db,Users,Blogs,Comments
from forms import LoginForm,RegisterForm,BlogTextForm,UserInfoForm,CommentForm,UpdatePasswdForm,SearchForm
from uuid import uuid1
from config import POSTS_PER_PAGE

import base64
import hashlib
import re
import datetime
import markdown2

COOKIE_NAME = 'lvconl'

def md5(args):
    pwd = hashlib.md5(bytes('admin',encoding='utf-8'))
    pwd.update(bytes(args,encoding='utf-8'))
    return pwd.hexdigest()

def checkUser():
    id = ''
    user = ''
    if 'id' in session:
        id = session['id']
    if id == '':
        id = request.cookies.get(COOKIE_NAME)
    users = Users.query.filter_by(id=id).all()
    if len(users) == 0:
        user = ''
    else:
        user = users[0]
    return user

@app.route('/',methods = ['GET','POST'])
def index(page = 1):
    user = checkUser()
    page = request.args.get('page',1,type = int)
    pagination = Blogs.query.order_by(Blogs.created_at.desc()).paginate(page,per_page = POSTS_PER_PAGE,error_out = False)
    blogs = pagination.items
    return render_template(
        "index.html",
        blogs = blogs,
        user = user,
        base64=base64,
        pagination = pagination
    )
@app.route('/blog/<id>',methods=['GET','POST'])
def read_blog(id):
    user = checkUser()
    blogs = Blogs.query.filter_by(id = id).all()
    if len(blogs) == 0:
        blog = ''
    else:
        blog = blogs[0]
    comments = Comments.query.filter_by(blog_id= id).order_by(Comments.created_at.desc()).all()
    blog.htmlcontent = markdown2.markdown(blog.content)
    form = CommentForm()
    if request.method == 'GET':
        return render_template(
            "blog.html",
            blog = blog,
            user = user,
            comments = comments,
            base64=base64,
            form = form,
        )
    if request.method == 'POST':
        content = form.comment.data
        comment = Comments(id = str(uuid1()),blog_id = blog.id,blog_name = blog.name,user_id = user.id,user_name = user.name,user_image = user.image,content = content)
        db.session.add(comment)
        db.session.commit()
        return redirect('/blog/'+blog.id)


@app.route('/login',methods = ["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.name.data
        password = form.password.data
        remember = form.remember.data
        users = Users.query.filter_by(email=email).all()
        if len(users) == 0:
            error = '*用户不存在'
        else:
            user = users[0]
            if user.passwd == md5(password):
                response = make_response('''<script>location.href='/';</script>''')
                if remember is True:
                    outdate = datetime.datetime.today() + datetime.timedelta(days=30)
                    response.set_cookie(COOKIE_NAME,user.id,expires = outdate)
                    return response
                else:
                    session['id'] = user.id
                    return redirect('/')
            else:
                error = '*密码错误'
        return render_template(
            'login.html',
            error = error,
            form = form
        )
    else:
        return render_template(
        "login.html",
        form = form
    )

@app.route('/signout')
def signout():
    if not 'id' in session:
        response = make_response('''<script>location.href='/';</script>''')
        response.delete_cookie(COOKIE_NAME)
        return response
    else:
        session['id'] = ''
        return redirect('/')


@app.route('/register',methods = ['GET','POST'])
def register():
    form = RegisterForm()
    if request.method == 'GET':
        return render_template(
            'register.html',
            form = form
        )
    name = form.name.data
    email = form.email.data
    password = form.password.data
    password1 = form.password1.data
    if name == '':
        error = '*用户名不能为空'
        return render_template(
            'register.html',
            form = form,
            error = error
        )
    if not re.match(r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}\.[com,cn,net]{1,3}$',email):
        error = '*暂不支持此格式的邮箱'
        return render_template(
            'register.html',
            form=form,
            error=error
        )
    if len(password) < 6:
        error = '*密码长度过短'
        return render_template(
            'register.html',
            form=form,
            error=error
        )
    if password != password1:
        error = '*两次输入密码不一致'
        return render_template(
            'register.html',
            form=form,
            error=error
        )
    users = Users.query.filter_by(email = email).all()
    if len(users) > 0:
        error = '*账号已存在'
        return render_template(
            'register.html',
            form=form,
            error=error
        )
    passwd = md5(password)
    user = Users(id = str(uuid1()),email = email,passwd = passwd,name = name)
    db.session.add(user)
    db.session.commit()
    response = make_response('''<script>location.href='/';</script>''')
    response.set_cookie(COOKIE_NAME,user.id)
    return response

@app.route('/blogs/create',methods = ['GET','POST'])
def blog_create():
    user = checkUser()
    if user == '':
        return redirect('/')
    form = BlogTextForm()
    if request.method == 'GET':
        return render_template(
            'blog_edit.html',
            form = form,
            user = user,
            base64=base64
        )
    if request.method == 'POST':
        name = form.name.data
        summary = form.summary.data
        content = form.content.data
        blog = Blogs(id = str(uuid1()),user_id = user.id,user_name = user.name,name = name,summary = summary,content = content)
        db.session.add(blog)
        db.session.commit()
        return redirect('/myblogs')

@app.route('/blogs')
def manage_blogs():
    user = checkUser()
    if user == '' or user.admin == 0:
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = Blogs.query.order_by(Blogs.created_at.desc()).paginate(page, per_page=5, error_out=False)
    blogs = pagination.items
    return render_template(
        'manage_blogs.html',
        blogs = blogs,
        user = user,
        base64=base64,
        pagination = pagination
    )

@app.route('/blogs/delete/<id>')
def blog_delete(id):
    user = checkUser()
    if user == '':
        return redirect('/')
    comment = Comments.query.filter_by(blog_id = id).all()
    blog = Blogs.query.filter_by(id = id).all()[0]
    db.session.delete(comment)
    db.session.delete(blog)
    db.session.commit()
    if user.admin == 1:
        return redirect('/blogs')
    else:
        return redirect('/myblogs')

@app.route('/blogs_edit/<id>',methods = ['GET','POST'])
def blog_edit(id):
    user = checkUser()
    if user == '':
        return redirect('/')
    form = BlogTextForm()
    blog = Blogs.query.filter_by(id=id).all()[0]
    if request.method == 'GET':
        form.name.data = blog.name
        form.summary.data = blog.summary
        form.content.data = blog.content
        return render_template(
            'blog_edit.html',
            form = form,
            base64 = base64
        )
    if request.method == 'POST':
        name = form.name.data
        summary = form.summary.data
        content = form.content.data
        Blogs.query.filter_by(id = id).update({'name':name,'summary':summary,'content':content})
        db.session.commit()
        return redirect('/')

@app.route('/user/edit',methods = ['GET','POST'])
def user_edit():
    user = checkUser()
    if user == '':
        return redirect('/')
    form = UserInfoForm()
    if request.method == 'GET':
        return render_template(
            'user_edit.html',
            form = form,
            user = user,
            base64 = base64
        )
    if request.method == 'POST':
        name = form.name.data
        image = request.files['image'].read()
        Users.query.filter_by(id = user.id).update({'name':name,'image':image})
        Blogs.query.filter_by(user_id = user.id).update({'user_name':name,'user_image':image})
        Comments.query.filter_by(user_id = user.id).update({'user_name':name,'user_image':image})
        db.session.commit()
        return redirect('/')

@app.route('/user/<id>')
def user(id):
    user = checkUser()
    user_info = Users.query.filter_by(id = id).all()[0]
    user_blog = Blogs.query.filter_by(user_id = id).order_by(Blogs.created_at.desc()).limit(3).all()
    user_comment = Comments.query.filter_by(user_id = id).order_by(Comments.created_at.desc()).limit(3).all()
    return render_template(
        'user_index.html',
        user = user,
        user_info = user_info,
        user_blog = user_blog,
        user_comment = user_comment,
        base64 = base64
    )

@app.route('/updatepasswd',methods = ['GET','POST'])
def updatepasswd():
    user = checkUser()
    if user == '':
        return redirect('/')
    form = UpdatePasswdForm()
    if request.method == 'GET':
        return render_template(
            'updatepasswd.html',
            user = user,
            base64 = base64,
            form = form
        )
    if request.method == 'POST':
        email = form.email.data
        originalPasswd = form.originalPasswd.data
        alterPasswd = form.alterPasswd.data
        reAlterPasswd = form.reAlterPasswd.data
        if not email == user.email:
            error = '邮箱错误'
            return render_template(
                'updatepasswd.html',
                user=user,
                base64=base64,
                form=form,
                error = error
            )
        if not md5(originalPasswd) == user.passwd:
            error = '原密码错误'
            return render_template(
                'updatepasswd.html',
                user=user,
                base64=base64,
                form=form,
                error = error
            )
        if alterPasswd != reAlterPasswd:
            error = '两次输入密码不一致'
            return render_template(
                'updatepasswd.html',
                user=user,
                base64=base64,
                form=form,
                error = error
            )
        Users.query.filter_by(id = user.id).update({'passwd':md5(alterPasswd)})
        db.session.commit()
        signout()
        return redirect('/')

@app.route('/myblogs',methods = ['GET','POST'])
def myblogs(page = 1):
    user = checkUser()
    if user == '':
        return redirect('/')
    page = request.args.get('page', 1, type=int)
    pagination = Blogs.query.filter_by(user_id = user.id).order_by(Blogs.created_at.desc()).paginate(page, per_page=5, error_out=False)
    blogs = pagination.items
    return render_template(
        'person_blog.html',
        user=user,
        base64 = base64,
        blogs = blogs,
        pagination = pagination
    )

@app.route('/mycomments',methods = ['GET','POST'])
def mycomments(page = 1):
    user = checkUser()
    if user == '':
        return redirect('/')
    page = request.args.get('page',1,type = int)
    pagination = Comments.query.filter_by(user_id = user.id).order_by(Comments.created_at.desc()).paginate(page,per_page = 6,error_out = False)
    comments = pagination.items
    return render_template(
        'person_comment.html',
        base64 = base64,
        comments = comments,
        user = user,
        pagination = pagination
    )

@app.route('/comment/<id>')
def delete_comment(id):
    user = checkUser()
    if user == '':
        return redirect('/')
    comment = Comments.query.filter_by(id = id).all()[0]
    db.session.delete(comment)
    db.session.commit()
    return redirect('/mycomments')

@app.route('/comments')
def comments(page = 1):
    user = checkUser()
    if user == '' or user.admin == 0:
        return redirect('/')
    page = request.args.get('page',1,type = int)
    pagination = Comments.query.order_by(Comments.created_at.desc()).paginate(page,per_page = 6,error_out = False)
    comments = pagination.items
    return render_template(
        'manage_comments.html',
        user = user,
        base64 = base64,
        comments = comments,
        pagination = pagination
    )