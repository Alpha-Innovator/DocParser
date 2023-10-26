from collections import defaultdict
import os
from PIL import Image
from typing import Dict, List
import numpy as np
import cv2

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTComponent, LTFigure, LTLine

from logger import logger
from rendering import envs
from annotation.layout import geometry
from config import config

log = logger.get_logger(__name__)


def generate_bb(filename: str, laparams=None) -> Dict[int, List[LTComponent]]:
    """
    Generate a bounding box dictionary for each page in a PDF file.

    Args:
        filename (str): The path to the PDF file.
        laparams (Optional[LAParams]): The layout analysis parameters.
            Defaults to None.

    Returns:
        Dict[int, List[LTComponent]]: A dictionary where the keys are the page
            indices and the values are lists of bounding boxes.

    Note:
        the bounding boxes are in the form of (x0, y0, x1, y1), where (x0, y0)
        is the lower_left corner and (x1, y1) is the upper_right corner.

        The origin of the coordinate system is the lower-left corner
        of the each page.

    See:
        https://pdfminersix.readthedocs.io/en/latest/topic/converting_pdf_to_text.html#layout-analysis-algorithm
    """
    file_elements = {}
    if laparams is None:
        laparams = LAParams()
    page_layouts = extract_pages(filename, laparams=laparams)
    for page_index, page_layout in enumerate(page_layouts):
        file_elements[page_index] = []
        file_elements[page_index].append(page_layout)
        # TODO: extract te color
        for element in page_layout:
            file_elements[page_index].append(element)

    file_elements = geometry.merge_bb(file_elements)
    return file_elements


def get_category(image: Image.Image, element: LTComponent) -> int:
    if isinstance(element, LTLine):
        if element.stroking_color == 0:
            return config.name2category["Others"]
        else:
            # TODO: add log to check if line is table or algorithm
            return config.name2category["Table"]

    x0, y0, x1, y1 = element.bbox
    roi = image.crop((x0, y0, x1, y1))

    roi_array = np.array(roi)
    hsv_roi = cv2.cvtColor(roi_array, cv2.COLOR_RGB2HSV)

    count = 0
    category = config.name2category["Others"]
    for key, value in config.category2hsv_bound.items():
        lower, upper = value
        mask = cv2.inRange(hsv_roi, lower, upper)
        if np.sum(mask) > count:
            count = np.sum(mask)
            category = key

    return category


def color_to_category(
    image: Image.Image,
    page_elements: List[LTComponent],
) -> list:
    """
    Generate a dictionary mapping the index of each element
    in the page_elements list to its corresponding category index.

    Args:
        image (PIL.Image.Image): The image object representing the page.
        page_elements (List[LTComponent]): A list of page elements.

    Returns:
        Dict[int, int]: A dictionary mapping the index of
        each element to its corresponding category index.
    """
    result = []

    for index, element in enumerate(page_elements):
        if index == 0:  # skip the LTPage element
            result.append(config.name2category["Others"])
            continue
        if isinstance(element, LTFigure):
            result.append(config.name2category["Figure"])
            continue

        result.append(get_category(image, element))

    return result


def generate_category_info(filename, main_directory, geometry_info):
    rendered_path = os.path.join(main_directory, "colored")
    category_info = defaultdict(list)  # map of bb index to category
    for page_index in geometry_info.keys():
        page_image_path = os.path.join(
            rendered_path, f"{filename}_rendered_colored_page_{page_index}.png"
        )
        page_image = Image.open(page_image_path)

        category_info[page_index] = color_to_category(
            page_image, geometry_info[page_index]
        )
        page_image.close()

    return category_info


def generate_geometry_info(main_directory, filename):
    rendered_path = os.path.join(main_directory, "colored")
    rendered_pdf = os.path.join(rendered_path, f"{filename}_rendered_colored.pdf")
    laparams = LAParams(**config.config["laparams"])
    file_elements = generate_bb(rendered_pdf, laparams)

    # generate object detection info
    geometry_info = defaultdict(list)  # geometry info member of COCO
    for page_index, page_elements in file_elements.items():
        page_image_path = os.path.join(
            rendered_path, f"{filename}_rendered_colored_page_{page_index}.png"
        )
        page_image = Image.open(page_image_path)
        geometry_info[page_index] = geometry.transform(page_elements, page_image)
        page_image.close()

    return geometry_info


def filter_results(geometry_info, category_info):
    f_geometry_info = defaultdict(list)
    f_category_info = defaultdict(list)
    for page_index, page_elements in geometry_info.items():
        for index, element in enumerate(page_elements):
            # TODO: make this list robust
            if category_info[page_index][index] in [
                config.name2category[env] for env in envs.complex_env_list
            ]:
                continue
            f_geometry_info[page_index].append(element)
            f_category_info[page_index].append(category_info[page_index][index])

    return f_geometry_info, f_category_info


def run(main_directory, filename):
    # generate geometry info
    geometry_info = generate_geometry_info(main_directory, filename)

    # generate category info
    category_info = generate_category_info(filename, main_directory, geometry_info)

    # filter results
    geometry_info, category_info = filter_results(geometry_info, category_info)

    return geometry_info, category_info
