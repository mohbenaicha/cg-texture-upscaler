import albumentations as A
import torch
from tqdm import tqdm
import time
import torch.nn
import os
from torch.utils.data import Dataset, DataLoader
import numpy as np
import config
from PIL import Image
import cv2


class MyImageFolder(Dataset):
    def __init__(self, root_dir):
        super(MyImageFolder, self).__init__()
        self.data = []
        self.root_dir = root_dir
        self.class_names = os.listdir(root_dir)

        for index, name in enumerate(self.class_names):
            files = os.listdir(os.path.join(root_dir, name))
            self.data += list(zip(files, [index] * len(files)))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        img_file, label = self.data[index]
        root_and_dir = os.path.join(self.root_dir, self.class_names[label])

        image = cv2.imread(os.path.join(root_and_dir, img_file))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        both_transform = config.both_transforms(image=image)["image"]
        
        if config.SUPER_RES:
            src = config.lowres_transform(image=both_transform)["image"]
            trg = config.highres_transform(image=both_transform)["image"]
        else: 
            src = config.blur_transform(image=both_transform)["image"]
            trg = config.clear_transform(image=both_transform)["image"]
        
        return src, trg


def test():
    dataset = MyImageFolder(root_dir="data/")
    loader = DataLoader(dataset, batch_size=8)

    for src, trg in loader:
        print(src.shape)
        print(trg.shape)
