import json
import os
import webbrowser

from bs4 import BeautifulSoup


class Generator2:
    def __init__(self, path):
        self.path = path
        self.file_name = path + '/elements.json'

        self.json = []
        self.html = ""
        self.read_json()
        self.reset_dimensions()
        self.gridsystem()
        self.generate_html()
        self.save_html()

    def read_json(self):
        with open(self.file_name) as json_file:
            self.json = json.load(json_file)

    def reset_dimensions(self):
        for index, i in enumerate(self.json):
            x = (i['x'] // 20) * 20
            self.json[index]['x'] = x

            y = (i['y'] // 20) * 20
            self.json[index]['y'] = y

            height = (i['height'] // 20) * 20
            self.json[index]['height'] = height

            width = (i['width'] // 20) * 20
            self.json[index]['width'] = width

            y1 = y - (height / 2)
            y2 = y + (height / 2)
            x1 = x - (width / 2)
            x2 = x + (width / 2)
            self.json[index]['y1'] = y1
            self.json[index]['y2'] = y2
            self.json[index]['x1'] = x1
            self.json[index]['x2'] = x2

    def gridsystem(self):
        z = self.json.copy()
        for i in range(0, 1000, 90):
            for index, el1 in enumerate(z):
                for el2 in self.json:
                    if el1 == el2:
                        continue
                    if el1['x1'] <= i <= el2['x2'] and el1['x2'] >= i >= el2['x1']:
                        if el1['type'] == 'Vertical Navbar' or el1['type'] == 'Horizontal Navbar':
                            continue
                        if el2['type'] == 'Vertical Navbar' or el2['type'] == 'Horizontal Navbar':
                            continue
                        if 90 > el2['y1'] - el1['y2'] > 0:
                            if el1['type'] == 'column':
                                el1['elements'].append(el2)
                                el1['y2'] = el2['y2']
                                z[index] = el1
                                self.json.remove(el2)
                                z.remove(el2)
                            else:
                                elements = {
                                    'type': 'column',
                                    'y1': el1['y1'],
                                    'y2': el2['y2'],
                                    'x1': el1['x1'],
                                    'x2': el1['x2'],
                                    'elements': [
                                        el1,
                                        el2
                                    ]
                                }
                                z.append(elements)
                                if el1 in z:
                                    z.remove(el1)
                                if el2 in z:
                                    z.remove(el2)
                                if el1 in self.json:
                                    self.json.remove(el1)
                                if el2 in self.json:
                                    self.json.remove(el2)


        m = []
        for i in range(0, 2000, 50):
            lst = []
            for j in z:
                if type(j) == list:
                    continue
                if j['y1'] <= i <= j['y2']:
                    if j['type'] == 'Vertical Navbar' or j['type'] == 'Horizontal Navbar':
                        continue
                    lst.append(j)
            if len(lst) > 1:
                lst = sorted(lst, key=lambda k: (int(k['y1']), int(k["x1"])))
                elements = {
                    'type': 'row',
                    'y1': lst[0]['y1'],
                    'y2': lst[-1]['y2'],
                    'x1': lst[0]['x1'],
                    'x2': lst[-1]['x2'],
                    'elements': lst
                }
                m.append(elements)
                for item in lst:
                    z.remove(item)
        elements = z + m
        elements = sorted(elements, key=lambda k: (int(k['y1']), +int(k["x1"])))
        self.json = elements

    def generate_html(self):
        for i in self.json:
            if i['type'] == "row":
                if len(i['elements']) == 2:
                    self.html += self.grid6x2(i['elements'])
                else:
                    self.html += self.grid4x3(i['elements'])
            elif i['type'] == "Button":
                self.html += (self.button(i['body']))
            elif i['type'] == "Paragraph":
                self.html += self.grid12x1(self.p())
            elif i['type'] == "Link":
                self.html += (self.Link())
            elif i['type'] == "Text":
                self.html += (self.h2(i['body']))
            elif i['type'] == "Vertical Navbar":
                self.html += (self.navbar())
            elif i['type'] == "Chart Line":
                self.html += (self.p())
            elif i['type'] == "Check Box":
                self.html += (self.input())
            elif i['type'] == "Horizontal Navbar":
                self.html += self.navbar()
            elif i['type'] == "Image Circle":
                self.html += (self.image())
            elif i['type'] == "Image Rectangular":
                self.html += (self.image())
            elif i['type'] == "Input text.html":
                self.html += (self.input())
            elif i['type'] == "Map":
                self.html += (self.h2(i['body']))
            elif i['type'] == "Paragraph":
                self.html += (self.navbar())
            elif i['type'] == "Radio Button":
                self.html += (self.navbar())
            elif i['type'] == "Search":
                self.html += (self.navbar())
            elif i['type'] == "Textarea":
                self.html += (self.navbar())
            elif i['type'] == "Stack bar":
                self.html += (self.navbar())
            elif i['type'] == "Youtube":
                self.html += (self.youtube(i['url']))

    def getType(self, i):
        if type(i) == list:
            str = ""
            for x in i:
                str += self.getType(x)
            return str

        if i['type'] == "column":
            return self.getType(i['elements'])
        if i['type'] == "Button":
            return self.button(i['body'])
        elif i['type'] == "Paragraph":
            return self.p()
        elif i['type'] == "input.html":
            return self.input()
        elif i['type'] == "Link":
            return self.Link()
        elif i['type'] == "Text":
            return self.h2(i['body'])
        elif i['type'] == "Vertical Navbar":
            return self.navbar()
        elif i['type'] == "Chart Line":
            return self.p()
        elif i['type'] == "Check Box":
            return self.input()
        elif i['type'] == "Horizontal Navbar":
            return self.navbar()
        elif i['type'] == "Image Circle":
            return self.image()
        elif i['type'] == "Image Rectangular":
            return self.image()
        elif i['type'] == "Input text.html":
            return self.input()
        elif i['type'] == "Map":
            return self.h2(i['body'])
        elif i['type'] == "Paragraph":
            return self.p()
        elif i['type'] == "Radio Button":
            return self.navbar()
        elif i['type'] == "Search":
            return self.navbar()
        elif i['type'] == "Textarea":
            return self.navbar()
        elif i['type'] == "Stack bar":
            return self.navbar()
        elif i['type'] == "Youtube":
            return self.youtube(i['url'])

    def save_html(self):
        f = open(self.path + '/index.html', 'w')
        html_template = f"""<!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.1/dist/css/bootstrap.min.css">
            <title>Hello, world!</title>
          </head>
          <body>
          {self.html}
            <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.1/dist/js/bootstrap.min.js"></script>
          </body>
        </html>
        """
        html_template = BeautifulSoup(html_template, 'html.parser')
        f.write(str(html_template.prettify()))
        f.close()
        webbrowser.open_new_tab("file://"+self.path+"/index.html")

    def changeTextType(self):
        pass

    def navbar(self):
        return """
        <nav class="navbar navbar-expand-lg navbar-light bg-light">
  <a class="navbar-brand" href="#">Navbar</a>
  <button.html class="navbar-toggler" type="button.html" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button.html>

  <div class="collapse navbar-collapse" id="navbarSupportedContent">
    <ul class="navbar-nav mr-auto">
      <li class="nav-item active">
        <a class="nav-link" href="#">Home <span class="sr-only">(current)</span></a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="#">Link</a>
      </li>
      <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button.html" data-toggle="dropdown" aria-expanded="false">
          Dropdown
        </a>
        <div class="dropdown-menu" aria-labelledby="navbarDropdown">
          <a class="dropdown-item" href="#">Action</a>
          <a class="dropdown-item" href="#">Another action</a>
          <div class="dropdown-divider"></div>
          <a class="dropdown-item" href="#">Something else here</a>
        </div>
      </li>
      <li class="nav-item">
        <a class="nav-link disabled">Disabled</a>
      </li>
    </ul>

  </div>
</nav>
        """


    def button(self, text):
        return f"""<button.html type="button.html" class="btn btn-primary">{text}</button.html>"""

    def p(self):
        return """
            <p>Lorem Ipsum is simply dummy text.html of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text.html ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.</p>
        """

    def h2(self, text):
        return f"""<h2>{text}</h2>"""

    def input(self):
        return """<input.html type="text.html" class="form-control">"""

    def image(self):
        return """<img src="https://www.mantruckandbus.com/fileadmin/media/bilder/02_19/219_05_busbusiness_interviewHeader_1485x1254.jpg" class="img-fluid" alt="Responsive image.html">"""

    def Link(self):
        return """<a href="www.google.com">Google</a>"""

    def youtube(self,url):
        return f"""<iframe width="100%" height="315" src="https://www.youtube.com/embed/{url}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>"""

    def grid12x1(self, i):
        return f"""
            <div class="container my-5">
            <div class="row">
                {i}
            </div>
            </div>
        """

    def grid6x2(self, i):
        i = sorted(i, key=lambda k: (int(k['x1'])))
        i = list(i)
        x = """
        <div class="container my-5">        
        <div class="row">
            <div class="col-md-6">"""
        for j in [i[0]]:
            x += self.getType(j)
        x += """</div>
            <div class="col-md-6">"""
        for j in [i[1]]:
            x += self.getType(j)
        x += """</div>
        </div>
        </div>
        """
        return x

    def grid4x3(self, i):
        i = sorted(i, key=lambda k: (int(k['y1']), +int(k["x1"])))
        i = list(i)
        x = """
        <div class="container my-5">        
        <div class="row">
            <div class="col-md-4">"""
        for j in [i[0]]:
            x += self.getType(j)
        x += """</div>
            <div class="col-md-4">"""
        for j in [i[1]]:
            x += self.getType(j)
        x += """</div>
        <div class="col-md-4">"""
        for j in [i[2]]:
            x += self.getType(j)
        x += """</div>
        </div>
        </div>
        """
        return x
