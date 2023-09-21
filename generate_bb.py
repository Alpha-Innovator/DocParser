import os
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple
import json
import argparse
import datetime
import numpy as np
import cv2

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTPage, LTComponent, LTFigure, LTLine

from logger import logger
from rendering.utils import export_to_json, load_json
from layout import geometry
from reading_annotation_generator import generate_reading_annotation

log = logger.setup_app_level_logger(file_name="app_debug.log", mode="a")

config = load_json("config.json")
name2category = {v: k for k, v in config["category_name"]}
category2name = {k: v for k, v in config["category_name"]}
category2color = {k: v for k, v in config["category_color"]}

category2hsv_bound = {}  # category: (lower_bound, upper_bound)
for k, v in category2color.items():
    rgb_color = tuple(v)

    # Convert RGB to HSV
    hsv_color = cv2.cvtColor(np.uint8([[rgb_color]]), cv2.COLOR_RGB2HSV)[0][0]

    lower_bound = np.array(
        [
            hsv_color[0] - config["hue_range"],
            hsv_color[1] - config["saturation_range"],
            hsv_color[2] - config["value_range"],
        ]
    )
    upper_bound = np.array(
        [
            hsv_color[0] + config["hue_range"],
            hsv_color[1] + config["saturation_range"],
            hsv_color[2] + config["value_range"],
        ]
    )

    category2hsv_bound[k] = (lower_bound, upper_bound)


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

    return file_elements


def generate_geometry_annotation(
    page_image: Image.Image,
    page_elements: List[LTComponent],
    category_info: Dict[int, int],
) -> Image.Image:
    """
    Generate an annotation for an image.

    Args:
        page_image (Image.Image): The image to annotate.
        page_elements (List[LTComponent]): A list of elements to be annotated.

    Returns:
        Image.Image: The annotated image.
    """
    draw = ImageDraw.Draw(page_image)
    # use `locate .ttf` to find the available fonts
    font = ImageFont.truetype(
        config["annotation_image_font_type"], config["annotation_image_font_size"]
    )

    for index, element in enumerate(page_elements):
        category = category_info[index]
        draw.rectangle(element.bbox, outline="red")
        draw.text(
            (element.bbox[0], element.bbox[1]),
            category2name[category],
            fill=(255, 0, 0),
            font=font,
        )

    return page_image


def get_category(image: Image.Image, element: LTComponent) -> int:
    if isinstance(element, LTLine):
        if element.stroking_color == 0:
            return name2category["Others"]
        else:
            # TODO: add log to check if line is table or algorithm
            return name2category["Table"]

    x0, y0, x1, y1 = element.bbox
    roi = image.crop((x0, y0, x1, y1))

    roi_array = np.array(roi)
    hsv_roi = cv2.cvtColor(roi_array, cv2.COLOR_RGB2HSV)

    count = 0
    category = name2category["Others"]
    for key, value in category2hsv_bound.items():
        lower, upper = value
        mask = cv2.inRange(hsv_roi, lower, upper)
        if np.sum(mask) > count:
            count = np.sum(mask)
            category = key

    log.debug(f"element={element}, category: {category}")
    return category


def color_to_category(
    image: Image.Image,
    page_elements: List[LTComponent],
) -> Dict[int, int]:
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
    result = {}

    for index, element in enumerate(page_elements):
        if index == 0:  # skip the LTPage element
            result[index] = name2category["Others"]
            continue
        if isinstance(element, LTFigure):
            result[index] = name2category["Figure"]
            continue

        result[index] = get_category(image, element)

    return result


def export_to_coco(
    file_elements: Dict[int, List[LTComponent]],
    image_infos: Dict[int, str],
    category_infos: Dict[int, Dict[int, int]],
    filename: str,
) -> None:
    result = {
        "info": {
            "year": 2023,
            "version": "1.0",
            "description": "Visually Rich Document Understanding data process",
            "contributor": "manual",
            "url": "https://github.com/MaoSong2022/vrdu_data_process",
            "date_created": f"{datetime.datetime.now()}",
        },
        "licenses": [  # TODO: modify this
            {
                "url": "http://creativecommons.org/licenses/by/2.0/",
                "id": 4,
                "name": "Attribution License",
            }
        ],
        "images": [],
        "annotations": [],
        "categories": [
            {"id": index, "name": category}
            for index, category in config["category_name"]
        ],
    }
    for page_index, page_elements in file_elements.items():
        for index, element in enumerate(page_elements):
            if isinstance(element, LTPage):
                image = {
                    "id": page_index,
                    "width": element.bbox[2] - element.bbox[0],
                    "height": element.bbox[3] - element.bbox[1],
                    "file_name": image_infos[page_index],
                    "coco_url": "",  # TODO: modify this
                    "date_captured": "",  # TODO: modify this
                    "flickr_url": "",  # TODO: modify this
                    "license": 0,  # TODO: modify this
                }
                result["images"].append(image)
            else:
                width = element.bbox[2] - element.bbox[0]
                height = element.bbox[3] - element.bbox[1]
                annotation = {
                    "id": index,
                    "image_id": page_index,
                    "category_id": category_infos[page_index][index],
                    "segmentation": [],
                    "bbox": [element.bbox[0], element.bbox[1], width, height],
                    "area": width * height,
                    "iscrowd": 0,
                }
                result["annotations"].append(annotation)

    with open(filename, "w") as f:
        json.dump(result, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--file_name", type=str, required=True)
    args = parser.parse_args()
    main_directory = args.path
    filename = args.file_name

    rendered_path = os.path.join(main_directory, "rendered")
    result_path = os.path.join(main_directory, "result")

    rendered_pdf = os.path.join(rendered_path, f"{filename}_rendered.pdf")

    laparams = LAParams(**config["laparams"])
    file_elements = generate_bb(rendered_pdf, laparams)
    file_elements = geometry.merge_bb(file_elements)

    # generate object detection info
    geometry_infos = {}  # geometry info member of COCO
    image_infos = {}  # annotation image info member of COCO
    category_infos = {}  # map of bb index to category
    for page_index, page_elements in file_elements.items():
        page_image_path = os.path.join(
            rendered_path, f"{filename}_rendered_page_{page_index}.jpg"
        )
        page_image = Image.open(page_image_path)

        transformed_page_elements = geometry.transform(page_elements, page_image)
        category_infos[page_index] = color_to_category(
            page_image, transformed_page_elements
        )
        annotated_image = generate_geometry_annotation(
            page_image, transformed_page_elements, category_infos[page_index]
        )

        image_name = f"{filename}_annotation_page_{page_index}.jpg"
        annotated_image_path = os.path.join(result_path, image_name)
        image_infos[page_index] = annotated_image_path
        annotated_image.save(annotated_image_path, "JPEG")
        geometry_infos[page_index] = transformed_page_elements

    layout_json_file = os.path.join(result_path, "layout_annotation.json")
    export_to_coco(
        geometry_infos, image_infos, category_infos, filename=layout_json_file
    )

    # generate text annotation info
    result = generate_reading_annotation(geometry_infos, category_infos)
    text_json_file = os.path.join(result_path, "reading_annotation.json")
    export_to_json(result, text_json_file)


if __name__ == "__main__":
    main()
