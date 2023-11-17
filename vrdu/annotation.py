from collections import defaultdict
import os
import glob
from typing import Any, Dict, List, Iterator
import matplotlib.pyplot as plt
import numpy as np
from skimage.measure import label, regionprops
from PIL import Image, ImageDraw, ImageFont
import re
from tqdm import tqdm

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTFigure, LTPage
from vrdu import utils


from vrdu.block import Block, BoundingBox
from vrdu.config import config, envs
from vrdu import logger
from vrdu.utils import load_json

log = logger.get_logger(__name__)


def get_image_pairs(dir1: str, dir2: str):
    """
    Generate a list of image pairs based on the directories provided.

    Parameters:
        dir1 (str): The directory path to the first set of images.
        dir2 (str): The directory path to the second set of images.

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

    log.debug(f"rendered_png_files: {rendered_png_files}")
    log.debug(f"changed_png_files: {changed_png_files}")
    if len(rendered_png_files) != len(changed_png_files):
        raise FileNotFoundError("Wrong image path or file name or page index!")

    page_indices = []
    for i in range(len(rendered_png_files)):
        file_name = os.path.basename(rendered_png_files[i])
        page_index = int(os.path.splitext(file_name)[0])
        page_indices.append(int(page_index))

    image_pairs = list(zip(page_indices, rendered_png_files, changed_png_files))
    return image_pairs


class LayoutAnnotation:
    def __init__(
        self,
        directory: str,
        text_info: Dict[str, List[str]],
    ) -> None:
        self.directory = directory
        self.background_dir = os.path.join(directory, "white")
        self.env_dirs = self.get_matching_subdirectories()
        self.layout_metadata = None
        self.text_info = text_info
        # TODO: move this to config
        self.threshold = 0.3
        self.ppi = 72
        self.ONE_INCH = 72.27

    def extract_pdf_layouts(self) -> Iterator[LTPage]:
        laparams = LAParams(**config.config["laparams"])
        rendered_pdf = os.path.join(self.directory, "colored/paper.pdf")
        page_layouts = extract_pages(rendered_pdf, laparams=laparams)
        return page_layouts

    def extract_layout_metadata(self):
        path = os.path.dirname(self.directory)
        log_file = os.path.join(path, "paper_colored.log")
        regex_pattern = r"\[vrdu_data_process: The (.*) is: ([-+]?\d+\.\d+)pt\]"

        extracted_data = {}

        with open(log_file, "r", encoding="latin-1") as file:
            log_content = file.read()

            for match in re.findall(regex_pattern, log_content):
                key = match[0]
                value = float(match[1])
                extracted_data[key] = value

        return extracted_data

    def parse_metadata(self, pdf_layouts: Iterator[LTPage]) -> None:
        pt2px = self.ppi / self.ONE_INCH

        layout_metadata = dict()

        # get metadata from log file
        path = os.path.dirname(self.directory)
        log_file = os.path.join(path, "paper_colored.log")
        regex_pattern = r"\[vrdu_data_process: The (.*) is: ([-+]?\d+\.\d+)pt\]"

        with open(log_file, "r", encoding="latin-1") as file:
            log_content = file.read()

            for match in re.findall(regex_pattern, log_content):
                key = match[0]
                value = float(match[1])
                layout_metadata[key] = value

        textwidth = layout_metadata["textwidth"]
        columnsep = layout_metadata["columnsep"]
        columnwidth = layout_metadata["columnwidth"]
        # textwidth = n * columnwidth + (n - 1) * columnsep
        num_columns = round((textwidth + columnsep) / (columnwidth + columnsep))
        layout_metadata["num_columns"] = num_columns

        # https://www.overleaf.com/learn/latex/Page_size_and_margins
        element1 = self.ONE_INCH + layout_metadata["hoffset"]
        element3 = layout_metadata["oddsidemargin"]
        margin_width = element1 + element3
        layout_metadata["margin_width"] = margin_width

        for page_index, page_layout in enumerate(pdf_layouts):
            layout_metadata[page_index] = {}

            pdf_width, pdf_height = page_layout.width, page_layout.height
            layout_metadata[page_index]["pdf_width"] = pdf_width
            layout_metadata[page_index]["pdf_height"] = pdf_height

            page_image_path = os.path.join(self.directory, f"colored/{page_index}.png")
            with Image.open(page_image_path) as page_image:
                image_width, image_height = page_image.size
            layout_metadata[page_index]["image_width"] = image_width
            layout_metadata[page_index]["image_height"] = image_height

            px2img = image_height / pdf_height
            layout_metadata[page_index]["px2img"] = px2img
            layout_metadata[page_index]["separations"] = [0]

            # x is initialize as left boundary of a column minus a half of column separation width
            # this can make sure the separation is in the middle of two columns
            x = margin_width - 0.5 * columnsep
            for i in range(num_columns - 1):
                separation = x + columnwidth + columnsep
                layout_metadata[page_index]["separations"].append(
                    separation * pt2px * px2img
                )
                x += separation

            layout_metadata[page_index]["separations"].append(pdf_width * px2img)

        # layout_metadata["separations"].append(pdf_width * px2img)
        utils.export_to_json(
            layout_metadata, os.path.join(self.directory, "result/layout_metadata.json")
        )

        self.layout_metadata = layout_metadata

    def get_matching_subdirectories(self) -> List[str]:
        result = []
        for name in os.listdir(self.directory):
            if not os.path.isdir(os.path.join(self.directory, name)):
                continue
            if not any(name.startswith(prefix) for prefix in envs.complex_env_list):
                continue
            result.append(name)
        return result

    def extract_text_and_number(self, dir_name: str):
        match = re.search(r"(\D+)_(\d+)", dir_name)
        if match:
            text = match.group(1)
            number = int(match.group(2))
            return text, number
        else:
            return None, None

    def get_category(self, dir: str):
        dir_name = os.path.basename(dir)
        env_name, index = self.extract_text_and_number(dir_name)

        if env_name not in config.name2category:
            raise ValueError(f"Invalid directory name: {dir_name}")

        return config.name2category[env_name], index

    def generate_figure_bb(
        self, pdf_layouts: Iterator[LTPage]
    ) -> Dict[int, List[Block]]:
        text_info = load_json(os.path.join(self.directory, "result/texts.json"))

        layout_info = defaultdict(list)
        figure_list = []
        if "Figure" in text_info:
            figure_list = text_info["Figure"]
        index = 0

        for page_index, page_layout in enumerate(pdf_layouts):
            if index >= len(figure_list):
                continue

            for element in page_layout:
                # use only figures annotation result
                if not isinstance(element, LTFigure):
                    continue
                layout_info[page_index].append(
                    Block(
                        bounding_box=BoundingBox(*element.bbox),
                        page_index=page_index,
                        category=config.name2category["Figure"],
                        source_code=figure_list[index],
                    )
                )
                index += 1

        return layout_info

    def transform(self, layout_info: Dict[int, List[Block]]) -> None:
        for page_index in layout_info.keys():
            pdf_height = self.layout_metadata[page_index]["pdf_height"]
            px2img = self.layout_metadata[page_index]["px2img"]
            for index, element in enumerate(layout_info[page_index]):
                x0, y0, x1, y1 = element.bbox
                # flip the y-axis
                y0, y1 = pdf_height - y1, pdf_height - y0
                # scale
                width, height = element.width, element.height
                x0, y0 = x0 * px2img, y0 * px2img
                x1, y1 = x0 + width * px2img, y0 + height * px2img
                layout_info[page_index][index].bbox = BoundingBox(x0, y0, x1, y1)

    def generate_non_figure_bb(self) -> Dict[int, List[Block]]:
        layout_info = defaultdict(list)
        for dir_name in tqdm(self.env_dirs):
            log.debug(f"Processing {dir_name}")
            env_dir = os.path.join(self.directory, dir_name)
            image_pairs = get_image_pairs(env_dir, self.background_dir)
            category, index = self.get_category(dir_name)
            for image_pair in image_pairs:
                page_index = image_pair[0]

                image1_array = np.array(plt.imread(image_pair[1]), dtype=np.uint8)
                image2_array = np.array(plt.imread(image_pair[2]), dtype=np.uint8)

                diff_image = np.abs(image2_array - image1_array, dtype=np.uint8)
                labeled_image, num = label(diff_image > self.threshold, return_num=True)
                if num == 0:
                    continue

                regions = regionprops(labeled_image)
                bounding_boxes = [region.bbox for region in regions]

                if len(bounding_boxes) == 0:
                    continue

                # We do not consider the cross column tables.
                category_name = config.category2name[category]
                if category_name in envs.one_column_envs:
                    min_x = min(bounding_boxes, key=lambda x: x[1])[1]
                    min_y = min(bounding_boxes, key=lambda x: x[0])[0]
                    max_x = max(bounding_boxes, key=lambda x: x[4])[4]
                    max_y = max(bounding_boxes, key=lambda x: x[3])[3]

                    # element = LTComponent(bbox=(min_x, min_y, max_x, max_y))
                    element = Block(
                        bounding_box=BoundingBox(min_x, min_y, max_x, max_y),
                        source_code=self.text_info[category_name][index],
                        category=category,
                        page_index=page_index,
                    )
                    layout_info[page_index].append(element)
                    continue

                elements = []
                separations = self.layout_metadata[page_index]["separations"]
                for column in range(self.layout_metadata["num_columns"]):
                    column_boxes = [
                        bb
                        for bb in bounding_boxes
                        if bb[1] >= separations[column]
                        and bb[1] <= separations[column + 1]
                    ]
                    if not column_boxes:
                        continue
                    min_x = min(column_boxes, key=lambda x: x[1])[1]
                    min_y = min(column_boxes, key=lambda x: x[0])[0]
                    max_x = max(column_boxes, key=lambda x: x[4])[4]
                    max_y = max(column_boxes, key=lambda x: x[3])[3]

                    element = Block(
                        bounding_box=BoundingBox(min_x, min_y, max_x, max_y),
                        source_code=self.text_info[category_name][index],
                        category=category,
                        page_index=page_index,
                    )
                    if elements:
                        element.parent_block = elements[-1].block_id
                    elements.append(element)

                for element in elements:
                    layout_info[page_index].append(element)

        return layout_info

    def generate(self) -> Dict[int, List[Block]]:
        pdf_layouts = self.extract_pdf_layouts()
        self.parse_metadata(pdf_layouts)
        figure_layout_info = self.generate_figure_bb(pdf_layouts)
        self.transform(figure_layout_info)
        layout_info = self.generate_non_figure_bb()
        for page_index in layout_info.keys():
            layout_info[page_index].extend(figure_layout_info[page_index])
        return layout_info


def generate_reading_annotation(path: str, layout_info: Dict[int, List[Block]]):
    rendered_path = os.path.join(path, "colored")
    result_path = os.path.join(path, "result")
    reading_annotation = defaultdict(list)
    for page_index in layout_info.keys():
        page_image_path = os.path.join(rendered_path, f"{page_index}.png")
        page_image = Image.open(page_image_path)
        for block in layout_info[page_index]:
            if block.category == -1:  # the page itself is skipped
                continue
            cropped_image = page_image.crop(block.bbox)
            image_name = f"{config.category2name[block.category]}_{block.id}.png"
            image_path = os.path.join(result_path, image_name)
            cropped_image.save(image_path)
            reading_annotation[page_index].append(
                {"source_code": block.source_code, "image_path": image_path}
            )
        page_image.close()

    return reading_annotation


def generate_geometry_annotation(
    page_image: Image.Image, layout_elements: List[Block]
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
        config.config["annotation_image_font_type"],
        config.config["annotation_image_font_size"],
    )

    for index, element in enumerate(layout_elements):
        category = element.category
        if category == -1:  # the page itself is skipped
            continue
        draw.rectangle(element.bbox, outline=config.colors_map[category], width=3)
        draw.text(
            (element.bbox[0], element.bbox[1]),
            config.category2name[category],
            fill=(255, 0, 0),
            font=font,
        )

    return page_image


def generate_image_annotation(path, layout_info):
    rendered_path = os.path.join(path, "colored")
    result_path = os.path.join(path, "result")
    image_info = {}  # annotation image info member of COCO
    for page_index in layout_info.keys():
        page_image_path = os.path.join(rendered_path, f"{page_index}.png")
        page_image = Image.open(page_image_path)
        annotated_image = generate_geometry_annotation(
            page_image, layout_info[page_index]
        )
        image_name = f"{page_index}.png"
        annotated_image_path = os.path.join(result_path, image_name)
        image_info[page_index] = annotated_image_path
        annotated_image.save(annotated_image_path)
        page_image.close()

    return image_info
