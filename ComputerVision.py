import os
import cv2
import numpy as np
import json
from google.cloud import vision
import io
from Generator import Generator
from Predict import Predict

# import os
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:/D/projects/graduation/graduation.json"

class ComputerVision:

    def __init__(self, path, folder_name):
        self.path = os.path.dirname(os.path.abspath(__file__)) + '/static/elements/' + folder_name
        self.image = cv2.imread(path)
        self.path_image = path
        self.jsonelement = []
        self.jsontext = []
        self.json = []

        self.export_shape()
        self.detect_text()
        self.save_image()

        self.sort_elements()
        self.save_json()

    def export_shape(self):
        # read image.html
        img = self.image

        # preprocessing in image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        canny = cv2.Canny(blurred, 120, 255, 1)
        kernel = np.ones((5, 5), np.uint8)
        dilate = cv2.dilate(canny, kernel, iterations=1)

        # Find contours
        cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]

        elements = []
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            elements.append([x, y, w + x, h + y])

        # Remove included photos
        final_elements = elements.copy()
        for i in elements:
            ix1, iy1, ix2, iy2 = i
            for j in elements:
                jx1, jy1, jx2, jy2 = j
                if ix1 < jx1 and iy1 < jy1 and ix2 > jx2 and iy2 > jy2:
                    final_elements.remove(j)

        image_number = 0
        for m in final_elements:
            x, y, w, h = m
            w -= x
            h -= y
            element = {
                "type": "",
                "x1": x,
                "y1": y,
                "x2": (x + w),
                "y2": (y + h),
                "x": (x + x + w) // 2,
                "y": (y + y + h) // 2,
                "height": h,
                "width": w,
                "body": "",
            }
            self.jsonelement.append(element)
            image_number += 1

    def detect_text(self):
        client = vision.ImageAnnotatorClient()

        with io.open(self.path_image, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.text_detection(image=image)
        texts = response.text_annotations

        x = texts[0].description
        ps = x.splitlines()
        index = 1
        for p in ps:
            listx = []
            listy = []
            for word in p.split():
                text = texts[index]
                index += 1
                listx.extend([text.bounding_poly.vertices[0].x, text.bounding_poly.vertices[2].x])
                listy.extend([text.bounding_poly.vertices[0].y, text.bounding_poly.vertices[2].y])

            max_x, min_x, max_y, min_y = max(listx), min(listx), max(listy), min(listy)
            w = max_x - min_x
            h = max_y - min_y

            list_element = []
            # [x + 10 for x in i]
            for x in self.jsonelement:
                if min_x - 10 < x['x'] < max_x + 10:
                    if min_y - 10 < x['y'] < max_y + 10:
                        list_element.append(x)

            # check if button or link
            type = "Text"
            if len(list_element) == 1:
                element_width = (list_element[0]['props']['width'])
                text_width = w
                if element_width > text_width + 50:
                    type = "Button"
                    self.jsonelement.remove(list_element[0])
                    list_element[0]['body'] = p
                    list_element[0]['type'] = type
                    self.jsonelement.append(list_element[0])
                else:
                    type = "Link"
                    for x in list_element:
                        self.jsonelement.remove(x)
            else:
                for x in list_element:
                    self.jsonelement.remove(x)

            center_x = (max_x + min_x) // 2
            center_y = (max_y + min_y) // 2

            if type != "Button":
                self.jsontext.append({
                    "type": type,
                    "x1": min_x,
                    "y1": min_y,
                    "x2": max_x,
                    "y2": max_y,
                    "x": center_x,
                    "y": center_y,
                    "height": h,
                    "width": w,
                    "body": p,
                })

        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))

    def element_type(self):
        return Predict(self.path)

    def sort_elements(self):
        self.json = self.jsonelement + self.jsontext
        self.json = sorted(self.json, key=lambda k: (int(k['y']), int(k["x"])))

    def save_image(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        for index, element in enumerate(self.jsonelement):
            if element['type'] != "Button":
                h = element['height']
                y = element['y'] - h // 2
                w = element['width']
                x = element['x'] - w // 2
                y2 = y + h
                x2 = w + x
                image_dimensions = self.image[y:y2, x:x2]
                cv2.imwrite(self.path + "/{0}.png".format(index + 1), image_dimensions)

        elements = self.element_type()
        elements = elements.__list__()
        for index, element in enumerate(self.jsonelement):
            if element['type'] != "Button":
                element['type'] = elements[index]

    def save_json(self):
        for index, element in enumerate(self.json):
            self.json[index]['id'] = index
        with open(self.path + '/elements.json', 'w') as outfile:
            outfile.write(json.dumps(self.json, indent=2))

        Generator(self.path)
