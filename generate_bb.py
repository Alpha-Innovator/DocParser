import os
from PIL import Image, ImageDraw
from typing import Dict, List

from pdfminer.high_level import extract_pages

from logger import logger

log = logger.setup_app_level_logger(file_name="app_debug.log")


def generate_bb(filename: str) -> Dict[int, List]:
    """
    Generate a dictionary of elements from a given file.

    Args:
        filename (str): The name of the file to extract elements from.

    Returns:
        Dict[int, List]: A dictionary where the keys are page indices 
        and the values are lists of elements.
    """
    elements = {}
    page_layouts = extract_pages(filename)
    for page_index, page_layout in enumerate(page_layouts):
        elements[page_index] = []
        elements[page_index].append(page_layout)
        for element in page_layout:
            elements[page_index].append(element)

    return elements


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


def show_bb(image_path: str, elements: List) -> None:
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

    image.show()


def main():
    filename = os.path.expanduser("~/icml2022/example_paper.pdf")
    elements = generate_bb(filename)

    first_page = os.path.expanduser(
        "~/icml2022/output/original/example_paper_page_0.jpg"
    )
    show_bb(first_page, elements[0])


if __name__ == "__main__":
    main()
