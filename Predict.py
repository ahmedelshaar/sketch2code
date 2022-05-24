import os
import torch
from torchvision import transforms, models
from ResNet import ResNet50
import cv2



class Predict:

    def __init__(self, path):
        images = os.listdir(path)
        lst = []
        for i in images:
            lst.append(cv2.imread(path + "/" + i))

        labels = ['Chart Line', 'Check Box', 'Horizontal Navbar', 'Image', 'Image', 'Input',
                  'Map', 'Paragraph', 'Pie charts', 'Radio Box', 'Search', 'Stack bar', 'Textarea',
                  'Vertical Navbar', 'Youtube']

        model = ResNet50(num_classes=len(labels))
        model.load_state_dict(torch.load(os.path.dirname(os.path.abspath(__file__)) + "\model.pt"))

        transformer = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])

        for i in range(len(lst)):
            lst[i] = torch.unsqueeze(transformer(lst[i]), 0)

        batch = torch.Tensor(len(lst), 3, 224, 224)

        torch.cat(lst, out=batch)

        outputs = model(batch)
        _, pred = torch.max(outputs, 1)

        self.predictions_labels = []
        for i in pred:
            self.predictions_labels.append(labels[i])


    def __list__(self):
        return self.predictions_labels
