#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import app
from flask import render_template, request, url_for, redirect, session, send_file, send_from_directory
from app.api.api import API
from werkzeug.utils import secure_filename
from flask_dropzone import Dropzone
import os
import tempfile

cmd = API()
curr_path = []

@app.route('/')
@app.route('/index/', methods=['GET'])
def index():
    # For testing only
    #return render_template('prueba.html')

    data = cmd.list_dir(root=True)
    
    while curr_path:
        curr_path.pop()

    return render_template('index.html', title="MyCloud", items=data)

# This helps to include Script files into Jinja2 templates
@app.template_global()
def static_include(filename):
    with open(os.path.join(app.root_path, 'static/'+filename), 'r') as f:
        return f.read()

@app.route('/files/<title>', methods=['GET', 'POST'])
def file(title):
    type, content = cmd.get_file_content(title)
    if type == 'error':
        if not curr_path:
            data = cmd.list_dir(root=True)
        else:
            data = cmd.list_dir(dir=''.join(curr_path))
        return render_template('index.html', title="MyCloud", items=data, path=curr_path)
    
    # File
    elif type == 'file':
        with open('app/temp/'+title, "wb") as f:
            for c in content:
                f.write(c)
        return send_file('temp/'+title, as_attachment=True)
    
    # Directory
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


app.config.update(
    DROPZONE_UPLOAD_ON_CLICK=True,
    DROPZONE_REDIRECT_VIEW="index",
    DROPZONE_INPUT_NAME="file",
    DROPZONE_DEFAULT_MESSAGE="Either drag or click to upload files"

)
dropzone = Dropzone(app)
@app.route('/upload_file', methods=['POST'])
def upload_file():
    for key, f in request.files.items():
        if key.startswith('file'):
            cmd.store_file(f)
    
    if not curr_path:
        data = cmd.list_dir(root=True)
    else:
        data = cmd.list_dir(dir=''.join(curr_path))
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
