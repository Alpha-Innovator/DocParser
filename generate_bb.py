import os
from PIL import Image, ImageDraw
from typing import Dict, List, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTPage

from logger import logger

log = logger.setup_app_level_logger(file_name="app_debug.log")


def generate_bb(filename: str, laparams=None) -> Dict[int, List]:
    """
    Generate a dictionary of elements from a given file.

    Args:
        filename (str): The name of the file to extract elements from.

    Returns:
        Dict[int, List]: A dictionary where the keys are page indices
        and the values are lists of elements.
    """
    elements = {}
    if laparams is None:
        laparams = LAParams()
    page_layouts = extract_pages(filename, laparams=laparams)
    for page_index, page_layout in enumerate(page_layouts):
        elements[page_index] = []
        elements[page_index].append(page_layout)
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
        elements[index].bbox = (x0, y1, x1, y0)
    return elements


def generate_annotation(image_path: str, elements: List) -> Tuple[Image.Image, List]:
    """
    Display bounding boxes on an image.

    Parameters:
        image_path (str): The path to the image file.
        elements (List): A list of elements to draw bounding boxes on.

    Returns:
        None
    """
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    elements = transform(elements, image)
    for element in elements:
        draw.rectangle(element.bbox, outline="red")

    return image, elements


def export_to_coco(elements: Dict[int, List], filename: str):
    pass


def main():
    filename = os.path.expanduser("~/icml2022/example_paper.pdf")
    elements = generate_bb(filename)

    annotation_infos = {}
    for page_index, page_elements in elements.items():
        annotation_infos[page_index] = []
        page = os.path.expanduser(
            f"~/icml2022/output/original/example_paper_page_{page_index}.jpg"
        )
        image, transformed_elements = generate_annotation(page, elements[page_index])
        output = os.path.expanduser(
            f"~/icml2022/output/result/example_paper_page_{page_index}.jpg"
        )

        image.save(output, "JPEG")
        annotation_infos[page_index].append(transformed_elements)

    json_file = os.path.expanduser(
        f"~/icml2022/output/result/annotation.json"
    )
    export_to_coco(annotation_infos, filename=json_file)


if __name__ == "__main__":
    main()
