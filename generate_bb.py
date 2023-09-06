import os
from PIL import Image, ImageDraw
from typing import Dict, List, Tuple
import json
import argparse
import datetime

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTPage

from logger import logger

log = logger.setup_app_level_logger(file_name="app_debug.log")


def generate_bb(filename: str, laparams=None) -> Dict[int, List]:
    """
    Generate a bounding box dictionary for each page in a PDF file.

    Args:
        filename (str): The path to the PDF file.
        laparams (Optional[LAParams]): The layout analysis parameters.
            Defaults to None.

    Returns:
        Dict[int, List]: A dictionary where the keys are the page indices
            and the values are lists of bounding boxes.
    """
    elements = {}
    if laparams is None:
        laparams = LAParams()
    page_layouts = extract_pages(filename, laparams=laparams)
    for page_index, page_layout in enumerate(page_layouts):
        elements[page_index] = []
        elements[page_index].append(page_layout)
        # TODO: extract te color
        for element in page_layout:
            elements[page_index].append(element)

    return elements


def merge_bb():
    pass
    # 1. delete an element if this element is inside another element
    # 2. merge two elements if there is an overlap
    # 3. merge two elements if they lie on the same side
    #    and horizontally overlap


def transform(elements: List, image: Image.Image):
    """
    Transform the coordinates of elements based on the size of an image.
    It first flip the y-axis, then scale the width and height of the page
    to match the image

    Args:
        elements (List): A list of elements representing bounding boxes.
        image (Image.Image): The image to use for scaling.

    Returns:
        List: A list of elements with transformed coordinates.
    """
    image_width, image_height = image.size
    page_width, page_height = elements[0].bbox[2], elements[0].bbox[3]

    if image_width / page_width != image_height / page_height:
        raise Exception("image size and page size are not scaled")

    scale = image_width / page_width
    for index, element in enumerate(elements):
        x0, y0, x1, y1 = element.bbox
        # flip the y-axis
        y0, y1 = page_height - y1, page_height - y0
        # scale
        element_width = x1 - x0
        element_height = y1 - y0
        x0 = x0 * scale
        y0 = y0 * scale
        y1 = y0 + element_height * scale
        x1 = x0 + element_width * scale
        elements[index].bbox = (x0, y0, x1, y1)
    return elements


def generate_annotation(image_path: str,
                        elements: List) -> Tuple[Image.Image, List]:
    """
    Generate an annotation for an image.

    Args:
        image_path (str): The path to the image file.
        elements (List): A list of elements to be annotated.

    Returns:
        Tuple[Image.Image, List]: A tuple containing the annotated
            image and the list of annotated elements.
    """
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    elements = transform(elements, image)
    for element in elements:
        draw.rectangle(element.bbox, outline="red")

    return image, elements


def color_to_category(element):
    return 0


def export_to_coco(
    elements: Dict[int, List], image_infos: Dict[int, str], filename: str
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
            {"id": 0, "name": "Algorithm"},
            {"id": 1, "name": "Caption"},
            {"id": 2, "name": "Equation"},
            {"id": 3, "name": "Figure"},
            {"id": 4, "name": "Footnote"},
            {"id": 5, "name": "List"},
            {"id": 6, "name": "Others"},
            {"id": 7, "name": "Table"},
            {"id": 8, "name": "Text"},
            {"id": 9, "name": "Text-EQ", "supercategory": "Text"},
            {"id": 10, "name": "Title"},
        ],
    }
    for page_index, page_elements in elements.items():
        log.debug(f"page_index: {page_index}, page_elements: {page_elements}")
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
                    "category_id": color_to_category(element),  # TODO: modify this
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
    elements = generate_bb(rendered_pdf)
    merge_bb()

    annotation_infos = {}
    image_infos = {}
    for page_index, page_elements in elements.items():
        page = os.path.join(rendered_path, f"{filename}_rendered_page_{page_index}.jpg")
        image, transformed_elements = generate_annotation(page, page_elements)

        image_name = f"{filename}_annotation_page_{page_index}.jpg"
        annotated_image = os.path.join(result_path, image_name)
        image_infos[page_index] = annotated_image
        image.save(annotated_image, "JPEG")
        annotation_infos[page_index] = transformed_elements

    json_file = os.path.join(result_path, "annotation.json")
    export_to_coco(annotation_infos, image_infos, filename=json_file)


if __name__ == "__main__":
    main()
