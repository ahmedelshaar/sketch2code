import json
import os
import shutil

from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
import uuid

from ComputerVision import ComputerVision
from Generator import Generator


app = Flask(__name__)
app.config["SECRET_KEY"] = "sketch2code"
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, "static/sketch")


class UploadImage(FlaskForm):
    image = FileField('Upload Image')
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        if 'image' not in request.files:
            return 'there is no image in form!'

        name = uuid.uuid4().hex
        image = request.files['image']
        file_name = uuid.uuid4().hex + '.' + image.filename.split('.')[-1]
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
        ComputerVision(os.path.join(app.config['UPLOAD_FOLDER'], file_name), name)
        path = os.path.dirname(os.path.abspath(__file__)) + '/static/elements/' + name
        Generator(path)
        # return redirect(url_for('static', filename='elements/' + name + '/design/index.html')) # view
        # return redirect(url_for('editor2', name=name)) # old editor
        # return redirect(url_for('download', name=name))  # download
        return redirect(url_for('editor', name=name))

    form = UploadImage()
    return render_template('index.html', form=form)


@app.route('/download/<name>')
def download(name):
    pathname = app.root_path + '/static/elements/' + name + '/design'
    shutil.make_archive(pathname, 'zip', pathname)
    return redirect(url_for('static', filename='elements/' + name + '/design.zip'))


@app.route('/editor/<name>')
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
def save(name):
    pathname = app.root_path + '/static/elements/' + name + '/design/index.html'
    html_template = BeautifulSoup(request.get_json()['gjs-html'], 'html.parser')
    html_template.body.hidden = True
    for s in html_template.select('script'):
        s.extract()
    template = render_template('layouts/stander.html', html=html_template)

    f = open(pathname, "w")
    html_template = BeautifulSoup(template, 'html.parser')
    f.write(str(html_template.prettify()))
    f.close()
    return "done"


@app.route('/editor2/<name>')
def editor2(name):
    pathname = 'elements/' + name + '/elements.json'
    pathname = url_for('static', filename=pathname);
    with open(app.root_path + pathname, 'r') as f:
        data = json.load(f)
    return render_template('editor2.html', pathname=pathname, elements=data, name=name)


@app.route('/save2/<name>', methods=['POST'])
def save2(name):
    path = os.path.dirname(os.path.abspath(__file__)) + '/static/elements/' + name
    with open(path + '/elements.json', 'w') as outfile:
        outfile.write(json.dumps(request.get_json(), indent=2))
    Generator(path)
    return redirect(path + 'index.html')

if __name__ == "__main__":
    app.run(debug=True)