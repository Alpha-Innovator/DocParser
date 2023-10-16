import os
import glob
from typing import Dict
import matplotlib.pyplot as plt
import argparse
import numpy as np
from skimage.measure import label, regionprops
import re
from PIL import Image, ImageDraw
from tqdm import tqdm

from pdfminer.layout import LTComponent
from rendering.utils import load_json
from logger import logger

log = logger.get_logger(__name__)

config = load_json("config/config.json")

name2category = {v: k for k, v in config["category_name"]}
category2name = {k: v for k, v in config["category_name"]}


def get_image_pairs(dir1: str, dir2: str):
    """
    Generate a list of image pairs based on the directories provided.

    Parameters:
        dir1 (str): The directory path where the first set of images is located.
        dir2 (str): The directory path where the second set of images is located.

    Raises:
        FileNotFoundError: If the number of images in each directory does not
            match or if the page index in the file names does not match.

    Returns:
        list: A list of tuples representing the image pairs.
            Each tuple contains the page index, the path to the rendered image,
            and the path to the changed image.
    """
    file_pattern = os.path.join(dir1, "*.png")
    rendered_png_files = sorted(glob.glob(file_pattern))
    file_pattern = os.path.join(dir2, "*.png")
    changed_png_files = sorted(glob.glob(file_pattern))

    if len(rendered_png_files) != len(changed_png_files):
        raise FileNotFoundError("Wrong image path or file name or page index!")

    page_indices = []
    for i in range(len(rendered_png_files)):
        match = re.search(r"_(\d+)\.png$", rendered_png_files[i])
        page_index = match.group(1)
        page_indices.append(int(page_index))

    for i in range(len(changed_png_files)):
        match = re.search(r"_(\d+)\.png$", rendered_png_files[i])
        page_index = match.group(1)
        if int(page_index) != page_indices[i]:
            raise FileNotFoundError("Wrong image path or file name or page index!")

    image_pairs = list(zip(page_indices, rendered_png_files, changed_png_files))
    return image_pairs


def generate_bounding_box(image_pairs, threshold=0.3):
    result = {}
    for image_pair in image_pairs:
        page_index = image_pair[0]
        result[page_index] = []

        image1 = plt.imread(image_pair[1])
        image1_array = np.array(image1, dtype=np.uint8)

        image2 = plt.imread(image_pair[2])
        image2_array = np.array(image2, dtype=np.uint8)

        diff_image = np.abs(image2_array - image1_array, dtype=np.uint8)
        binary_image = diff_image > threshold
        labeled_image = label(binary_image)

        regions = regionprops(labeled_image)
        bounding_boxes = [region.bbox for region in regions]

        if len(bounding_boxes) == 0:
            continue

        min_x = min(bounding_boxes, key=lambda x: x[1])[1]
        min_y = min(bounding_boxes, key=lambda x: x[0])[0]
        max_x = max(bounding_boxes, key=lambda x: x[4])[4]
        max_y = max(bounding_boxes, key=lambda x: x[3])[3]

        element = LTComponent(bbox=(min_x, min_y, max_x, max_y))
        result[page_index].append(element)
        # result[page_index].append((min_x, min_y, max_x, max_y))

    return result


def show_annotation(image_pair, bounding_boxes):
    image_path = image_pair[2]
    original_image = Image.open(image_path)

    # Create a drawing object
    draw = ImageDraw.Draw(original_image)

    # Define the rectangle outline color (in RGB format)
    outline_color = (255, 0, 0)  # Red

    for bounding_box in bounding_boxes:
        x1, y1, x2, y2 = bounding_box

        # Draw the rectangle on the image
        draw.rectangle((x1, y1, x2, y2), outline=outline_color)

    original_image.save("output.png")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--directory",
        type=str,
        help="The directory path where the first set of images is located.",
    )
    args = parser.parse_args()
    main_directory = args.directory
    return main_directory


def get_matching_subdirectories(folder_path):
    subdirectories = [
        name
        for name in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, name))
        and (
            name.startswith("algorithm")
            or name.startswith("equation")
            or name.startswith("table")
        )
    ]
    return subdirectories


def generate_category(geometry_info: Dict, dir1: str):
    dir_name = os.path.basename(dir1)
    if dir_name.startswith("algorithm"):
        name = "Algorithm"
    elif dir_name.startswith("equation"):
        name = "Equation"
    elif dir_name.startswith("table"):
        name = "Table"
    else:
        raise ValueError("Invalid directory name")

    category_info = {key: [] for key in geometry_info.keys()}
    for page_index, page_elements in geometry_info.items():
        if not page_elements:
            continue
        for _ in range(len(page_elements)):
            category_info[page_index].append(name2category[name])
    return category_info


def run(main_directory):
    env_dirs = get_matching_subdirectories(main_directory)
    dir2 = os.path.join(main_directory, "white")

    geometry_info = {}
    category_info = {}
    for env_dir in tqdm(env_dirs):
        dir1 = os.path.join(main_directory, env_dir)
        log.debug(f"processing dir: {dir1}")
        image_pairs = get_image_pairs(dir1, dir2)
        geometry_annotation = generate_bounding_box(image_pairs)

        for key in geometry_annotation.keys():
            if key not in geometry_info:
                geometry_info[key] = []
            geometry_info[key].extend(geometry_annotation[key])

        category_annotation = generate_category(geometry_annotation, dir1)
        for key in geometry_annotation.keys():
            if key not in category_info:
                category_info[key] = []
            category_info[key].extend(category_annotation[key])

    return geometry_info, category_info
