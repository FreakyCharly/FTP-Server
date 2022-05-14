#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import app
from flask import render_template, request, url_for, redirect, session, jsonify, make_response
import json
import os
import hashlib
import re
import random
from datetime import datetime
from app.api.api import API

cmd = API()
curr_path = []

@app.route('/')
@app.route('/index/', methods=['GET'])
def index():
    data = cmd.list_dir(root=True)
    
    while curr_path:
        curr_path.pop()

    return render_template('index.html', title="MyCloud", items=data)

@app.route('/files/<title>', methods=['GET', 'POST'])
def file(title):
    type, content = cmd.get_file_content(title)
    if type == 'file':
        return render_template('file_content.html', title="MyCloud - See content", data=content, path=curr_path)
    else:
        curr_path.append('/'+title)
        return render_template('index.html', title="MyCloud", items=content, path=curr_path)


@app.route('/files/undo', methods=['GET'])
def undo():
    try:
        curr_path.pop()
        if not curr_path:
            data = cmd.list_dir(root=True)
        else:
            data = cmd.list_dir(dir=''.join(curr_path))
    except:
        data = cmd.list_dir(root=True)
    return render_template('index.html', title="MyCloud", items=data, path=curr_path)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Return template
    if request.method == 'GET':
        return render_template('login.html', title="MyCloud - Login")
    
    # Authenticate
    elif request.method == 'POST':
        pass


@app.route('/register', methods=['GET'])
def register():
    pass

@app.route('/logout', methods=['GET'])
def logout():
    pass
