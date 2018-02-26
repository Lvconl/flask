#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File  : ajax.py
# @Author: lvconl
# @Date  : 18-2-25
#@Software : PyCharm

from flask import request
from flask import Blueprint
from models import db,Users,Blogs,Comments

ajax = Blueprint('ajax',__name__)

@ajax.route('/blogs/delete')
def blog_delete():
    id = request.args.get("id")
    comments = Comments.query.filter_by(blog_id = id).all()
    blog = Blogs.query.filter_by(id = id).all()[0]
    for comment in comments:
        db.session.delete(comment)
    db.session.delete(blog)
    db.session.commit()
    return u'删除成功！'

@ajax.route('/comment/delete')
def comment_delete():
    id = request.args.get("id")
    comment = Comments.query.filter_by(id = id).all()[0]
    db.session.delete(comment)
    db.session.commit()
    return u'删除成功!'