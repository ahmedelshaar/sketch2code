import shutil
import uuid

from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, redirect, url_for, render_template, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from ComputerVision import ComputerVision
from marshmallow import Schema, fields, validates, validate, exceptions
from functools import wraps
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = "sketch2code"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, "static/sketch")

db = SQLAlchemy(app)
Migrate(app, db)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    projects = db.relationship('Project', cascade='all,delete', backref='user', lazy='dynamic')

    def __init__(self, first, last, email, password):
        self.first_name = first
        self.last_name = last
        self.email = email
        self.password = password

    def all_projects(self):
        return [project for project in self.projects]

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())
    last_update = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())
    folder_name = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, name, image, user_id, folder_name):
        self.name = name
        self.image = image
        self.folder_name = folder_name
        self.user_id = user_id


class UserSchema(Schema):
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    email = fields.Email()
    password = fields.String(required=True, validate=validate.Length(min=8))
    @validates("password")
    def validate_password(self, value):
        if len(value.strip()) < 8:
            raise exceptions.ValidationError("invalid password")

class ProjectSchema(Schema):
    name = fields.String(required=True)

    

#################### User routes ################
def required_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('id') is None:
            return redirect(url_for('signin'))
        else:
            current_user = User.query.filter_by(id=session.get('id')).first()
        return f(current_user, *args, **kwargs)

    return decorated

def required_logout(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('id') is not None:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
@required_login
def dashboard(user):
    user_projects = User.query.filter_by(id=user.id).first().all_projects()
    output = []
    for project in user_projects:
        pro = {
            "id": project.id,
            "name": project.name,
            "image": 'sketch/' + project.image,
            "folder_name": project.folder_name,
            "created_at": project.created_at,
            "last_update": project.last_update,
            "download": url_for('download', name=project.folder_name, _external=True),
            "editor": url_for('editor', name=project.folder_name, _external=True),
            "preview": url_for('preview', name=project.folder_name, _external=True)
        }
        output.append(pro)
    return render_template('dashboard.html', projects=output)


@app.route('/signup', methods=['GET','POST'])
@required_logout
def signup():
    if request.method == 'GET':
        return render_template('sign-up.html')

    data = request.values

    email = data['email']
    first_name = data['first_name']
    last_name = data['last_name']
    password = data['password']
    found = User.query.filter_by(email=email).first()
    if found:
        return render_template('sign-up.html', error='this email used before')

    hashed_password = generate_password_hash(password, method='sha256')
    new_user = User(first=first_name, last=last_name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    session["id"] = new_user.id
    return redirect(url_for('dashboard'))



@app.route("/signin", methods=['GET','POST'])
@required_logout
def signin():
    if request.method == 'GET':
        return render_template('sign-in.html')

    data = request.values

    email = data['email']
    password = data['password']
    hashed_password = generate_password_hash(password, method='sha256')
    found = User.query.filter_by(email=email).first()
    if found:
        if check_password_hash(hashed_password, password):
            session["id"] = found.id
            return redirect(url_for('dashboard'))
        return render_template('sign-in.html', error='This Email or Password invalid')

    return render_template('sign-in.html', error='This Email or Password invalid')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

################## project routes ##################
@app.route('/project/new', methods=['POST'])
@required_login
def add_project(user):
    name = request.values.get('name')
    image = request.files['image']
    folder_name = uuid.uuid4().hex
    file_name = folder_name + '.' + image.filename.split('.')[-1]
    path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    image.save(path)
    project = Project(name=name, image=file_name, folder_name=folder_name, user_id=user.id)
    ComputerVision(path, folder_name)
    db.session.add(project)
    db.session.commit()
    user_projects = User.query.filter_by(id=user.id).first().all_projects()
    output = []
    for project in user_projects:
        pro = {
            "id": project.id,
            "name": project.name,
            "image": 'sketch/' + project.image,
            "folder_name": project.folder_name,
            "created_at": project.created_at,
            "last_update": project.last_update,
            "download": url_for('download', name=project.folder_name, _external=True),
            "editor": url_for('editor', name=project.folder_name, _external=True),
            "preview": url_for('preview', name=project.folder_name, _external=True)
        }
        output.append(pro)
    return render_template('dashboard.html', projects=output, success="Add Project")


@app.route('/download/<name>')
@required_login
def download(user, name):
    project = Project.query.filter_by(folder_name=name, user_id=user.id).first()
    if project:
        pathname = app.root_path + '/static/elements/' + name + '/design'
        shutil.make_archive(pathname, 'zip', pathname)
        return redirect(url_for('static', filename='elements/' + name + '/design.zip'))
    user_projects = User.query.filter_by(id=user.id).first().all_projects()
    output = []
    for project in user_projects:
        pro = {
            "id": project.id,
            "name": project.name,
            "image": 'sketch/' + project.image,
            "folder_name": project.folder_name,
            "created_at": project.created_at,
            "last_update": project.last_update,
            "download": url_for('download', name=project.folder_name, _external=True),
            "editor": url_for('editor', name=project.folder_name, _external=True),
            "preview": url_for('preview', name=project.folder_name, _external=True)
        }
        output.append(pro)
    return render_template('dashboard.html', error="Not Allow", projects=output)

@app.route('/preview/<name>')
@required_login
def preview(user, name):
    project = Project.query.filter_by(folder_name=name, user_id=user.id).first()
    if project:
        return redirect(url_for('static', filename='elements/' + name + '/design/dashboard.html'))
    user_projects = User.query.filter_by(id=user.id).first().all_projects()
    output = []
    for project in user_projects:
        pro = {
            "id": project.id,
            "name": project.name,
            "image": 'sketch/' + project.image,
            "folder_name": project.folder_name,
            "created_at": project.created_at,
            "last_update": project.last_update,
            "download": url_for('download', name=project.folder_name, _external=True),
            "editor": url_for('editor', name=project.folder_name, _external=True),
            "preview": url_for('preview', name=project.folder_name, _external=True)
        }
        output.append(pro)
    return render_template('dashboard.html', error="Not Allow", projects=output)

@app.route('/editor/<name>')
@required_login
def editor(user, name):
    project = Project.query.filter_by(folder_name=name, user_id=user.id).first()
    if project:
        pathname = app.root_path + '/static/elements/' + name + '/design/dashboard.html'
        with open(pathname) as f:
            template = f.read()
        html_template = BeautifulSoup(template, 'html.parser')
        html_template.body.hidden = True
        html_template = str(html_template.body)
        html_template = "".join(line.strip() for line in html_template.split("\n"))
        return render_template('editor.html', html=html_template, name=name)
    user_projects = User.query.filter_by(id=user.id).first().all_projects()
    output = []
    for project in user_projects:
        pro = {
            "id": project.id,
            "name": project.name,
            "image": 'sketch/' + project.image,
            "folder_name": project.folder_name,
            "created_at": project.created_at,
            "last_update": project.last_update,
            "download": url_for('download', name=project.folder_name, _external=True),
            "editor": url_for('editor', name=project.folder_name, _external=True),
            "preview": url_for('preview', name=project.folder_name, _external=True)
        }
        output.append(pro)
    return render_template('dashboard.html', error="Not Allow", projects=output)


@app.route('/save/<name>', methods=['POST'])
@required_login
def save(user, name):
    project = Project.query.filter_by(folder_name=name, user_id=user.id).first()
    if project:
        project.last_update = datetime.datetime.now()
        db.session.add(project)
        db.session.commit()
        pathname = app.root_path + '/static/elements/' + name + '/design/dashboard.html'
        html_template = BeautifulSoup(request.get_json()['gjs-html'], 'html.parser')
        html_template.body.hidden = True
        template = render_template('layouts/stander.html', html=html_template, css=request.get_json()['gjs-css'])
        f = open(pathname, "w")
        html_template = BeautifulSoup(template, 'html.parser')
        f.write(str(html_template.prettify()))
        f.close()
        return jsonify({"message": "Saved"})
    return jsonify({"message": "Not Allow"})

@app.route('/project/delete/<id>')
@required_login
def delete_project(user, id):
    project = Project.query.filter_by(id=id, user_id=user.id).first()
    if project:
        db.session.delete(project)
        db.session.commit()
        output = []
        user_projects = User.query.filter_by(id=user.id).first().all_projects()
        for project in user_projects:
            pro = {
                "id": project.id,
                "name": project.name,
                "image": 'sketch/' + project.image,
                "folder_name": project.folder_name,
                "created_at": project.created_at,
                "last_update": project.last_update,
                "download": url_for('download', name=project.folder_name, _external=True),
                "editor": url_for('editor', name=project.folder_name, _external=True),
                "preview": url_for('preview', name=project.folder_name, _external=True)
            }
            output.append(pro)
        return render_template('dashboard.html', projects=output, success="Delete Project")
    output = []
    user_projects = User.query.filter_by(id=user.id).first().all_projects()
    for project in user_projects:
        pro = {
            "id": project.id,
            "name": project.name,
            "image": 'sketch/' + project.image,
            "folder_name": project.folder_name,
            "created_at": project.created_at,
            "last_update": project.last_update,
            "download": url_for('download', name=project.folder_name, _external=True),
            "editor": url_for('editor', name=project.folder_name, _external=True),
            "preview": url_for('preview', name=project.folder_name, _external=True)
        }
        output.append(pro)
    return render_template('dashboard.html', error="Not Allow", projects=output)



if __name__ == "__main__":
    app.run(debug=True)