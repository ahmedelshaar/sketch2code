import json
import os
import shutil

from bs4 import BeautifulSoup
from flask import render_template


class Generator:
    def __init__(self, path):
        self.path = path
        self.file_name = path + '/elements.json'
        self.navbar = False
        self.sidebar = False
        self.json = []
        self.html = ""
        self.read_json()
        self.reset_dimensions()
        self.gridsystem()
        self.generator()

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
            if i['type'] == "Vertical Navbar":
                self.sidebar = True
                self.json.remove(i)
            elif i['type'] == "Horizontal Navbar":
                self.navbar = True
                self.json.remove(i)

    def gridsystem(self):
        z = self.json.copy()
        for i in range(0, 5000, 90):
            for index, el1 in enumerate(z):
                for el2 in self.json:
                    if el1 == el2:
                        continue
                    if el1['x1'] <= i <= el2['x2'] and el1['x2'] >= i >= el2['x1']:
                        if 90 > el2['y1'] - el1['y2'] > 0:
                            if el1['type'] == 'Column':
                                el1['elements'].append(el2)
                                el1['y2'] = el2['y2']
                                z[index] = el1
                                self.json.remove(el2)
                                z.remove(el2)
                            else:
                                elements = {
                                    'type': 'Column',
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
        for i in range(0, 5000, 50):
            lst = []
            for j in z:
                # if type(j) == list:
                #     continue
                if j['y1'] <= i <= j['y2']:
                    lst.append(j)
            if len(lst) > 1:
                lst = sorted(lst, key=lambda k: (int(k['y1']), int(k["x1"])))
                elements = {
                    'type': 'Row',
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
        print(json.dumps(self.json, indent=2))

    def generator(self):
        elements_dic = {
            'Chart Line': 'inc/chart.html',
            'Check Box': 'inc/checkbox.html',
            'Image': 'inc/image.html',
            'Input': 'inc/input.html',
            'Map': 'inc/map.html',
            'Paragraph': 'inc/p.html',
            'Pie charts': 'inc/chart.html',
            'Radio Box': 'inc/radiobox.html',
            'Search': 'inc/search.html',
            'Stack bar': 'inc/chart.html',
            'Textarea': 'inc/textarea.html',
            'Youtube': 'inc/youtube.html',
            'Text': 'inc/text.html',
            'Button': 'inc/button.html',
            'Row': 'inc/row.html',
            'Column': 'inc/column.html',
        }

        template = ""
        if self.navbar and self.sidebar:
            template = render_template('layouts/sidebar_navbar.html', elements=self.json, get_type=elements_dic)
        if self.sidebar:
            template = render_template('layouts/sidebar.html', elements=self.json, get_type=elements_dic)
        elif self.navbar:
            template = render_template('layouts/navbar.html', elements=self.json, get_type=elements_dic)
        else:
            template = render_template('layouts/stander.html', elements=self.json, get_type=elements_dic)
        if not os.path.exists(self.path + "/design"):
            os.mkdir(self.path + "/design")
            shutil.copy(self.path + "/../../css/style.css", self.path + "/design")
            shutil.copy(self.path + "/../../js/main.js", self.path + "/design")
        f = open(self.path + "/design/index.html", "w")
        html_template = BeautifulSoup(template, 'html.parser')
        f.write(str(html_template.prettify()))
        f.close()
