import shutil
import uuid

from bs4 import BeautifulSoup
from flask import Flask, jsonify, request, make_response, redirect, url_for, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from ComputerVision import ComputerVision

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
    avatar = db.Column(db.String, nullable=False)
    gender = db.Column(db.String, nullable=False)
    projects = db.relationship('Project', cascade='all,delete', backref='user', lazy='dynamic')

    def __init__(self, first, last, email, password, avatar, gender):
        self.first_name = first
        self.last_name = last
        self.email = email
        self.password = password
        self.avatar = avatar
        self.gender = gender

    def all_projects(self):
        return [project for project in self.projects]

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())
    last_update = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, name, image, user_id):
        self.name = name
        self.image = image
        self.user_id = user_id


#################### User routes ################
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'token' in request.headers:
            token = request.headers['token']
            print(token)
        else:
            token = None
            print("xxx")

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
    email = request.values.get('email')
    first_name = request.values.get('first_name')
    last_name = request.values.get('last_name')
    password = request.values.get('password')
    gender = request.values.get('gender')
    avatar = "55"
    found = User.query.filter_by(email=email).first()
    if found:
        return jsonify({'message': 'this email used before'})

    password = password
    hashed_password = generate_password_hash(password, method='sha256')
    new_user = User(first=first_name, last=last_name, email=email, password=hashed_password,
                    gender=gender, avatar=avatar)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'new user added'})


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
            "created_at": project.created_at,
            "last_update": project.last_update
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
        "created_at": project.created_at,
        "last_update": project.last_update
    }
    return jsonify(output)


@app.route('/project/new', methods=['POST'])
@token_required
def add_project(current_user):
    name = request.values.get('name')
    if name is None or '':
        return jsonify({'message': 'Name is required'}), 400
    if 'image' not in request.files:
        return jsonify({'message': 'Image is Required'}), 400

    image = request.files['image']
    folder_name = uuid.uuid4().hex
    file_name = folder_name + '.' + image.filename.split('.')[-1]
    path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    image.save(path)
    project = Project(name=name, image=path, user_id=current_user.id)
    ComputerVision(path, folder_name)
    db.session.add(project)
    db.session.commit()
    return jsonify({
        "message": "new project added",
        "download": url_for('download', name=folder_name, _external=True),
        "editor": url_for('editor', name=folder_name, _external=True),
    })


@app.route('/download/<name>')
@token_required
def download(current_user, name):
    pathname = app.root_path + '/static/elements/' + name + '/design'
    shutil.make_archive(pathname, 'zip', pathname)
    return redirect(url_for('static', filename='elements/' + name + '/design.zip'))


@app.route('/editor/<name>')
# @token_required
def editor(name):
    pathname = app.root_path + '/static/elements/' + name + '/design/index.html'
    with open(pathname) as f:
        template = f.read()
    html_template = BeautifulSoup(template, 'html.parser')
    html_template.body.hidden = True
    html_template = str(html_template.body)
    html_template = "".join(line.strip() for line in html_template.split("\n"))
    return render_template('editor.html', html=html_template, name=name)


@app.route('/save/<name>', methods=['POST'])
# @token_required
def save( name):
    pathname = app.root_path + '/static/elements/' + name + '/design/index.html'
    html_template = BeautifulSoup(request.get_json()['gjs-html'], 'html.parser')
    html_template.body.hidden = True
    template = render_template('layouts/stander.html', html=html_template, css=request.get_json()['gjs-css'])
    f = open(pathname, "w")
    html_template = BeautifulSoup(template, 'html.parser')
    f.write(str(html_template.prettify()))
    f.close()
    return jsonify({"message": "Saved"})

# @app.route('/assets/<name>', methods=['POST'])
# # @token_required
# def assets(name):
#     pathname = app.root_path + '/static/elements/' + name + '/design'
#     image = request.files['image']
#     file_name = uuid.uuid4().hex + '.' + image.filename.split('.')[-1]
#     path = os.path.join(pathname, file_name)
#     image.save(path)
#     print(path)
#     return jsonify({"data": ['https://.../image.png', {
#       "src": 'https://.../image2.png',
#       "type": 'image',
#       "height": 100,
#       "width": 200,
#     }]})

@app.route('/projects/update/<id>', methods=['PUT'])
@token_required
def update_project(current_user, id):
    user_id = current_user.id
    project = Project.query.filter_by(id=id, user_id=user_id).first()

    data = request.get_json()
    project.name = data['name']
    project.image = data['image']
    project.last_update = datetime.datetime.now()
    db.session.add(project)
    db.session.commit()
    return jsonify({"message": "project updated"})


@app.route('/projects/delete/<id>', methods=['DELETE'])
@token_required
def delete_project(current_user, id):
    user_id = current_user.id
    project = Project.query.filter_by(id=id, user_id=user_id).first()

    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "project deleted"})


if __name__ == "__main__":
    app.run(debug=True)





