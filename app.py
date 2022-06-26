import email
import shutil
import uuid

from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, make_response, redirect, url_for, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from jsonschema import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
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
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'token' in request.headers:
            token = request.headers['token']
            # print(token)
        else:
            token = None
            # print("xxx")

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id=data['user']).first()
        except:
            return jsonify({'message': 'token is invalid'}), 403

        return f(current_user, *args, **kwargs)

    return decorated


@app.route("/unprotected")
def unprotected():
    return jsonify({"message": "Anyone Can view this!"})


@app.route("/protected")
@token_required
def protected(self):
    return jsonify({"message": "This is only available for people with valid tokens.!"})



@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    try:
        UserSchema().load(data)
    except exceptions.ValidationError as err:
        return jsonify(err.messages)

    email = data['email']
    first_name = data['first_name']
    last_name = data['last_name']
    password = data['password']
    # email = request.values.get('email')
    # first_name = request.values.get('first_name')
    # last_name = request.values.get('last_name')
    # password = request.values.get('password')
    found = User.query.filter_by(email=email).first()
    if found:
        return jsonify({'message': 'this email used before'}), 400

    password = password
    hashed_password = generate_password_hash(password, method='sha256')
    new_user = User(first=first_name, last=last_name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    token = jwt.encode({'user': new_user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=60)},
                        app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token.decode()})


@app.route("/login", methods=['POST'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could verif!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    user = User.query.filter_by(email=auth.username).first()
    if not user:
        return make_response('Could verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'user': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=60)},
                           app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token.decode()})

    return make_response('Could verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


######################## project routes #######################
@app.route('/projects')
@token_required
def get_all_projects(current_user):
    user_id = current_user.id
    user_projects = User.query.filter_by(id=user_id).first().all_projects()
    output = []
    for project in user_projects:
        pro = {
            "id": project.id,
            "name": project.name,
            "image": project.image,
            "folder_name": project.folder_name,
            "created_at": project.created_at,
            "last_update": project.last_update,
            "download": url_for('download', name=project.folder_name, _external=True),
            "editor": url_for('editor', name=project.folder_name, _external=True),
            "preview": url_for('preview', name=project.folder_name, _external=True)
        }
        output.append(pro)
    return jsonify(output)


@app.route('/projects/<id>', methods=['GET'])
@token_required
def get_one_project(current_user, id):
    user_id = current_user.id
    project = Project.query.filter_by(id=id, user_id=user_id).first()

    output = {
        "name": project.name,
        "image": project.image,
        "folder_name": project.folder_name,
        "created_at": project.created_at,
        "last_update": project.last_update,
        "download": url_for('download', name=project.folder_name, _external=True),
        "editor": url_for('editor', name=project.folder_name, _external=True),
        "preview": url_for('preview', name=project.folder_name, _external=True),
    }
    return jsonify(output)


@app.route('/project/new', methods=['POST'])
@token_required
def add_project(current_user):
    
    if not request.values.get('name'):
        return jsonify({'message': 'Name is Required'}), 400
    
    name = request.values.get('name')

    past_project = Project.query.filter_by(user_id=current_user.id, name=name).first()
    if past_project:
        return jsonify({'message': 'this name is already exist'}), 400

    if 'image' not in request.files:
        return jsonify({'message': 'Image is Required'}), 400

    image = request.files['image']
    folder_name = uuid.uuid4().hex
    file_name = folder_name + '.' + image.filename.split('.')[-1]
    path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    image.save(path)
    project = Project(name=name, image=path, folder_name=folder_name, user_id=current_user.id)
    ComputerVision(path, folder_name)
    db.session.add(project)
    db.session.commit()
    return jsonify({
        "message": "new project added",
        "download": url_for('download', name=folder_name, _external=True),
        "editor": url_for('editor', name=folder_name, _external=True),
        "preview": url_for('preview', name=folder_name, _external=True),
    })


@app.route('/download/<name>')
@token_required
def download(current_user, name):
    user_id = current_user.id
    project = Project.query.filter_by(folder_name=name, user_id=user_id).first()
    if project:
        pathname = app.root_path + '/static/elements/' + name + '/design'
        shutil.make_archive(pathname, 'zip', pathname)
        return redirect(url_for('static', filename='elements/' + name + '/design.zip'))
    return jsonify({"message": "Not Allow"})

@app.route('/preview/<name>')
@token_required
def preview(current_user, name):
    user_id = current_user.id
    project = Project.query.filter_by(folder_name=name, user_id=user_id).first()
    if project:
        return redirect(url_for('static', filename='elements/' + name + '/design/index.html'))
    return jsonify({"message": "Not Allow"})


@app.route('/editor/<name>')
@token_required
def editor(current_user, name):
    user_id = current_user.id
    project = Project.query.filter_by(folder_name=name, user_id=user_id).first()
    if project:
        pathname = app.root_path + '/static/elements/' + name + '/design/index.html'
        with open(pathname) as f:
            template = f.read()
        html_template = BeautifulSoup(template, 'html.parser')
        html_template.body.hidden = True
        html_template = str(html_template.body)
        html_template = "".join(line.strip() for line in html_template.split("\n"))
        return render_template('editor.html', html=html_template, name=name)
    return jsonify({"message": "Not Allow"})
    


@app.route('/save/<name>', methods=['POST'])
@token_required
def save(current_user, name):
    user_id = current_user.id
    project = Project.query.filter_by(folder_name=name, user_id=user_id).first()
    if project:
        project.last_update = datetime.datetime.now()
        db.session.add(project)
        db.session.commit()
        pathname = app.root_path + '/static/elements/' + name + '/design/index.html'
        html_template = BeautifulSoup(request.get_json()['gjs-html'], 'html.parser')
        html_template.body.hidden = True
        template = render_template('layouts/stander.html', html=html_template, css=request.get_json()['gjs-css'])
        f = open(pathname, "w")
        html_template = BeautifulSoup(template, 'html.parser')
        f.write(str(html_template.prettify()))
        f.close()
        return jsonify({"message": "Saved"})
    return jsonify({"message": "Not Allow"})


@app.route('/projects/update/<id>', methods=['PUT'])
@token_required
def update_project(current_user, id):
    user_id = current_user.id
    project = Project.query.filter_by(id=id, user_id=user_id).first()
    if project:
        data = request.get_json()
        try:
            ProjectSchema().load(data)
        except exceptions.ValidationError as err:
            return jsonify(err.messages)
        project.name = data['name']
        project.last_update = datetime.datetime.now()
        db.session.add(project)
        db.session.commit()
        return jsonify({"message": "project updated"})
    return jsonify({"message": "Not Allow"})


@app.route('/projects/delete/<id>', methods=['DELETE'])
@token_required
def delete_project(current_user, id):
    user_id = current_user.id
    project = Project.query.filter_by(id=id, user_id=user_id).first()
    if project:
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "project deleted"})
    return jsonify({"message": "Not Allow"})



if __name__ == "__main__":
    app.run(debug=True)





