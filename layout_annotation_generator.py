from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple

from pdfminer.layout import LAParams, LTPage, LTComponent, LTFigure, LTLine

from rendering.utils import load_json


class AnnotationGenerator:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.text_info = load_json(config["text_elements_file"])
        self.section_generator = self._list_generator(self.text_info["section"])
        self.text_annotation = []

    def _list_generator(self, list):
        for item in list:
            yield item

    def generate_annotation(
        self,
        page_image: Image.Image,
        page_elements: List[LTComponent],
        category_info: Dict[int, int],
    ) -> Image.Image:
        for index, element in enumerate(page_elements):
            category = category_info[index]
            name = category2name[category]
            self.generate_bb_annotation(page_image, element, name)
            self.generate_text_annotation(element, name)
        return page_image

    def generate_bb_annotation(self, page_image, element, name):
        draw = ImageDraw.Draw(page_image)
        # use `locate .ttf` to find the available fonts
        font = ImageFont.truetype(
            self.config["annotation_image_font_type"],
            self.config["annotation_image_font_size"],
        )

        draw.rectangle(element.bbox, outline="red")
        draw.text(
            (element.bbox[0], element.bbox[1]),
            name,
            fill=(255, 0, 0),
            font=font,
        )

    def generate_text_annotation(self, element, name):
        if name == "Others":
            return

        if name == "Section":
            self.generate_section_annotation(element)

    def generate_section_annotation(self, element):
        section_name = next(self.section_generator)
        self.text_annotation.append({})
