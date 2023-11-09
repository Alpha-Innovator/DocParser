from collections import defaultdict
import os
from PIL import Image
from typing import Dict, List

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTComponent, LTFigure

from annotation.reading.block import Block, BoundingBox
from logger import logger
from config import config

log = logger.get_logger(__name__)


def generate_bb(
    main_directory: str, filename: str, laparams=None
) -> Dict[int, List[LTComponent]]:
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
    rendered_path = os.path.join(main_directory, "colored")
    rendered_pdf = os.path.join(rendered_path, f"{filename}_rendered_colored.pdf")

    layout_info = defaultdict(list)
    page_layouts = extract_pages(rendered_pdf, laparams=laparams)

    for page_index, page_layout in enumerate(page_layouts):
        layout_info[page_index].append(
            Block(
                bounding_box=BoundingBox(*page_layout.bbox),
                page_index=page_index,
                category=-1,
            )
        )

        for element in page_layout:
            # use only figures annotation result
            if not isinstance(element, LTFigure):
                continue
            layout_info[page_index].append(
                Block(
                    bounding_box=BoundingBox(*element.bbox),
                    page_index=page_index,
                    category=config.name2category["Figure"],
                )
            )

    return layout_info


def transform(layout_info, main_directory, filename):
    rendered_path = os.path.join(main_directory, "colored")
    for page_index in layout_info.keys():
        page_image_path = os.path.join(
            rendered_path, f"{filename}_rendered_colored_page_{page_index}.png"
        )
        page_image = Image.open(page_image_path)
        image_width, image_height = page_image.size
        page_image.close()

        page_width = layout_info[page_index][0].width
        page_height = layout_info[page_index][0].height

        if abs(image_width / page_width - image_height / page_height) > 0.001:
            raise Exception("image size and page size are not scaled")

        pdf2image = image_width / page_width
        for index, element in enumerate(layout_info[page_index]):
            x0, y0, x1, y1 = element.bbox
            # flip the y-axis
            y0, y1 = page_height - y1, page_height - y0
            # scale
            pdf_width, pdf_height = element.width, element.height
            x0, y0 = x0 * pdf2image, y0 * pdf2image
            x1, y1 = x0 + pdf_width * pdf2image, y0 + pdf_height * pdf2image
            layout_info[page_index][index].bbox = BoundingBox(x0, y0, x1, y1)


def run(main_directory, filename):
    laparams = LAParams(**config.config["laparams"])
    layout_info = generate_bb(
        main_directory,
        filename,
        laparams,
    )
    transform(layout_info, main_directory, filename)

    return layout_info
