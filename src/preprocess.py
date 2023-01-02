import os

import numpy as np
from PIL import Image


TARGET_H = 512
TARGET_W = 320


def preprocess(image_path: str) -> None:
    img = Image.open(image_path)
    img_array = np.array(img)
    h, w, _ = img_array.shape
    if h == TARGET_H and w == TARGET_W:
        return

    img = img.crop((55, 37, 55 + 640, 37 + 1024))
    img = img.resize((TARGET_W, TARGET_H))
    img.save(image_path)


def main(data_dir: str) -> None:
    images = os.listdir(data_dir)

    for image in images:
        preprocess(os.path.join(data_dir, image))
