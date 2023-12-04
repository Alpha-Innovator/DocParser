from collections import defaultdict
import os
import glob
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
from skimage.measure import label, regionprops
from PIL import Image, ImageDraw, ImageFont
import re
from tqdm import tqdm

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTPage
from vrdu import utils


from vrdu.block import Block, BoundingBox
from vrdu.config import config, envs
from vrdu import logger

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

    if len(rendered_png_files) != len(changed_png_files):
        raise FileNotFoundError("Wrong image path or file name or page index!")

    page_indices = []
    for i in range(len(rendered_png_files)):
        file_name = os.path.basename(rendered_png_files[i])
        page_index = int(os.path.splitext(file_name)[0])
        page_indices.append(int(page_index))

    image_pairs = list(zip(page_indices, rendered_png_files, changed_png_files))
    return image_pairs


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
        draw.rectangle(element.bbox, outline=config.colors_map[str(category)], width=3)
        draw.text(
            (element.bbox[0], element.bbox[1]),
            config.category2name[category],
            fill=(255, 0, 0),
            font=font,
        )

    return page_image


class LayoutAnnotation:
    def __init__(self, path: str) -> None:
        output_dir = os.path.join(path, "output")
        self.directory = output_dir
        self.background_dir = os.path.join(output_dir, "white")
        self.env_dirs = self.get_matching_subdirectories()
        self.layout_metadata: Dict = {}
        self.text_info = utils.load_json(os.path.join(output_dir, "result/texts.json"))
        # TODO: move this to config
        self.threshold = 0.3
        self.ppi = 72
        self.ONE_INCH = 72.27

    def extract_pdf_layouts(self) -> List[LTPage]:
        rendered_pdf = os.path.join(self.directory, "colored/paper.pdf")
        page_layouts = extract_pages(rendered_pdf)
        return list(page_layouts)

    def parse_metadata(self, pdf_layouts: List[LTPage]) -> None:
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
        element2 = self.ONE_INCH + layout_metadata["voffset"]
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
            # TODO: consider the margin notes
            layout_metadata[page_index]["separations"].append(pdf_width * px2img)
            layout_metadata[page_index]["top_margin"] = element2 * pt2px * px2img

        # layout_metadata["separations"].append(pdf_width * px2img)
        utils.export_to_json(
            layout_metadata, os.path.join(self.directory, "result/layout_metadata.json")
        )

        self.layout_metadata = layout_metadata

    def get_matching_subdirectories(self) -> List[str]:
        result = []
        # TODO: move this to config
        prefix = "block_"
        for name in os.listdir(self.directory):
            if not os.path.isdir(os.path.join(self.directory, name)):
                continue
            if not name.startswith(prefix):
                continue
            result.append(name)
        return result

    def get_category(self, env_orders: List[str], dir: str):
        dir_name = os.path.basename(dir)
        # TODO: move this to config
        prefix = "block_"
        order_id = int(dir_name[len(prefix) :])
        env_name = env_orders[order_id]

        index = -1
        for i, name in enumerate(env_orders):
            if name == env_name:
                index += 1
            if i == order_id:
                break

        suffix = "_color"
        env_name = env_name[: -len(suffix)]

        if env_name not in config.name2category:
            raise ValueError(f"Invalid directory name: {dir_name}")

        return config.name2category[env_name], index

    def generate_figure_bb(self, pdf_layouts: List[LTPage]) -> Dict[int, List[Block]]:
        layout_info = defaultdict(list)
        for page_index, page_layout in enumerate(pdf_layouts):
            for element in page_layout:
                # use only figures annotation result
                if not isinstance(element, LTFigure):
                    continue
                layout_info[page_index].append(
                    Block(
                        bounding_box=BoundingBox(*element.bbox),
                        page_index=page_index,
                        category=config.name2category["Figure"],
                        # currently, figure block will have no source code match
                        source_code="",
                    )
                )

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
        env_orders = utils.load_json(
            os.path.join(self.directory, "result/env_orders.json")
        )
        for dir_name in tqdm(sorted(self.env_dirs)):
            log.debug(f"Processing {dir_name}")
            env_dir = os.path.join(self.directory, dir_name)
            image_pairs = get_image_pairs(env_dir, self.background_dir)
            category, index = self.get_category(env_orders, dir_name)
            log.debug(f"category: {category}, index: {index}")

            elements = []
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

                # We do not consider the cross column case for these envs.
                category_name = config.category2name[category]
                if category_name in envs.one_column_envs:
                    element = Block(
                        bounding_box=BoundingBox.from_list(bounding_boxes),
                        source_code=self.text_info[category_name][index],
                        category=category,
                        page_index=page_index,
                    )
                    if elements:
                        element.parent_block = elements[-1].block_id
                    elements.append(element)
                    continue

                # consider possible cross column case
                separations = self.layout_metadata[page_index]["separations"]
                top_margin = self.layout_metadata[page_index]["top_margin"]
                for column in range(self.layout_metadata["num_columns"]):
                    # min_x: bb[1], min_y: bb[0], max_x: bb[4], max_y: bb[3]
                    column_boxes = [
                        bb
                        for bb in bounding_boxes
                        if bb[1] >= separations[column]
                        and bb[1] <= separations[column + 1]
                        and bb[0] >= top_margin
                    ]
                    if not column_boxes:
                        continue

                    element = Block(
                        bounding_box=BoundingBox.from_list(column_boxes),
                        source_code=self.text_info[category_name][index],
                        category=category,
                        page_index=page_index,
                    )
                    if elements:
                        element.parent_block = elements[-1].block_id
                    elements.append(element)

            for element in elements:
                layout_info[element.page_index].append(element)

        return layout_info

    def generate_layout_info(self) -> Dict[int, List[Block]]:
        pdf_layouts = self.extract_pdf_layouts()
        self.parse_metadata(pdf_layouts)
        layout_info = self.generate_non_figure_bb()
        figure_layout_info = self.generate_figure_bb(pdf_layouts)
        self.transform(figure_layout_info)
        for page_index in layout_info.keys():
            layout_info[page_index].extend(figure_layout_info[page_index])
        return layout_info

    def generate_reading_annotation(self, layout_info: Dict[int, List[Block]]):
        rendered_path = os.path.join(self.directory, "colored")
        result_path = os.path.join(self.directory, "result")
        reading_annotation = defaultdict(list)
        count = 0
        for page_index in layout_info.keys():
            page_image_path = os.path.join(rendered_path, f"{page_index}.png")
            page_image = Image.open(page_image_path)
            for block in layout_info[page_index]:
                cropped_image = page_image.crop(block.bbox)

                image_name = "block_" + str(count).zfill(4) + ".png"
                count += 1
                image_path = os.path.join(result_path, image_name)
                cropped_image.save(image_path)
                reading_annotation[page_index].append(
                    {
                        "source_code": block.source_code,
                        "image_path": image_name,
                        "category": block.category,
                    }
                )
            page_image.close()

        reading_annotation["categories"] = [
            {"id": index, "name": category}
            for index, category, _ in config.config["category_name"]
        ]

        return reading_annotation

    def generate_image_annotation(self, layout_info: Dict[int, List[Block]]):
        rendered_path = os.path.join(self.directory, "colored")
        result_path = os.path.join(self.directory, "result")
        image_info = {}  # annotation image info member of COCO
        for page_index in layout_info.keys():
            page_image_path = os.path.join(rendered_path, f"{page_index}.png")
            page_image = Image.open(page_image_path)
            annotated_image = generate_geometry_annotation(
                page_image, layout_info[page_index]
            )
            image_name = "page_" + str(page_index).zfill(4) + ".png"
            annotated_image_path = os.path.join(result_path, image_name)
            image_info[page_index] = image_name
            annotated_image.save(annotated_image_path)
            page_image.close()

        return image_info

    def extract_title_name(self, title):
        # TODO: move this to utils.py
        match = re.search(
            r"\\(chapter|section|subsection|subsubsection)(\*?){(.*)}", title
        )
        if match:
            return match.group(1)
        else:
            return ""

    def _compute_overlap(self, layout_info):
        result = []
        total_area, total_overlap, total_blocks = 0, 0, 0
        for page_index in layout_info.keys():
            blocks = layout_info[page_index]
            blocks.sort(key=lambda block: block.bbox.x0)

            area, overlap = 0, 0
            for i in range(len(blocks)):
                area += blocks[i].bbox.area()
                for j in range(i + 1, len(blocks)):
                    if blocks[j].bbox.x0 > blocks[i].bbox.x1:
                        break
                    overlap += blocks[i].bbox.overlap(blocks[j].bbox)

            result.append(
                {
                    "page": page_index,
                    "num_blocks": len(blocks),
                    "area": area,
                    "overlap": overlap,
                    "ratio": 0 if area == 0 else overlap / area,
                }
            )
            total_area += area
            total_overlap += overlap
            total_blocks += len(blocks)

        result.append(
            {
                "page": "total",
                "num_blocks": total_blocks,
                "area": total_area,
                "overlap": total_overlap,
                "ratio": 0 if total_area == 0 else total_overlap / total_area,
            }
        )

        return result

    def generate_order_annotation(self, layout_info: Dict[int, List[Block]]):
        relation_types = ["adj", "identical", "sub", "ref"]

        sortable_envs = ["Title", "Text", "Text-EQ", "Equation", "Footnote", "List"]
        sortable_catgory = [config.name2category[name] for name in sortable_envs]
        category2name = config.category2name

        sortable_elements = [
            block
            for page_index in layout_info.keys()
            for block in layout_info[page_index]
            if block.category in sortable_catgory
        ]
        # TODO: move this to config
        relation_map = {
            ("Text", "Text"): "adj",
            ("Text", "Text-EQ"): "adj",
            ("Text", "Equation"): "adj",
            ("Text", "List"): "adj",
            ("Text", "Footnote"): "ref",
            ("Text-EQ", "Text"): "adj",
            ("Text-EQ", "Text-EQ"): "adj",
            ("Text-EQ", "Equation"): "adj",
            ("Text-EQ", "List"): "adj",
            ("Text-EQ", "Footnote"): "ref",
            ("Equation", "Text"): "adj",
            ("Equation", "Text-EQ"): "adj",
            ("Equation", "Equation"): "adj",
            ("Equation", "List"): "adj",
            ("Equation", "Footnote"): "ref",
            ("List", "Text"): "adj",
            ("List", "Text-EQ"): "adj",
            ("List", "Equation"): "adj",
            ("List", "List"): "adj",
            ("List", "Footnote"): "ref",
            ("Title", "Text"): "sub",
            ("Title", "Text-EQ"): "sub",
            ("Title", "Equation"): "sub",
            ("Title", "List"): "sub",
            ("Title", "Footnote"): "ref",
            ("chapter", "chapter"): "adj",
            ("chapter", "section"): "sub",
            ("section", "section"): "adj",
            ("section", "subsection"): "sub",
            ("subsection", "subsection"): "adj",
            ("subsection", "subsubsection"): "sub",
            ("subsubsection", "subsubsection"): "adj",
        }

        result = []
        annotations = []

        for index, element in enumerate(sortable_elements):
            if index == 0:
                result.append(element)

            elif category2name[element.category] == "Title":
                while result and category2name[result[-1].category] != "Title":
                    result.pop()

                cur_title = self.extract_title_name(element.source_code)
                while (
                    result
                    and (self.extract_title_name(result[-1].source_code), cur_title)
                    not in relation_map
                ):
                    result.pop()

                if result:
                    prev_title = self.extract_title_name(result[-1].source_code)
                    annotations.append(
                        {
                            "type": relation_map.get(
                                (prev_title, cur_title),
                                "unknown",
                            ),
                            "from": element.block_id,
                            "to": result[-1].block_id,
                        }
                    )
                result.append(element)
            elif category2name[element.category] == "Footnote":
                if result:
                    annotations.append(
                        {
                            "type": "ref",
                            "from": result[-1].block_id,
                            "to": element.block_id,
                        }
                    )

            else:
                prev_element = result[-1]
                annotations.append(
                    {
                        "type": relation_map.get(
                            (
                                category2name[prev_element.category],
                                category2name[element.category],
                            ),
                            "unknown",
                        ),
                        "from": element.block_id,
                        "to": result[-1].block_id,
                    }
                )

                result.append(element)

        return annotations

    def generate_quality_report(self, layout_info):
        result = {}
        result["num_pages"] = max(layout_info.keys())
        result["num_columns"] = self.layout_metadata["num_columns"]
        result["category_quality"] = []

        total_reading, total_geometry = 0, 0
        for key, value in self.text_info.items():
            # currently, ignore graphics
            if key == config.name2category["Figure"]:
                continue

            reading_count = len(value)
            geometry_count = 0
            for page_index, blocks in layout_info.items():
                for block in blocks:
                    # only major block is counted
                    if (
                        block.category == config.name2category[key]
                        and block.parent_block is None
                    ):
                        geometry_count += 1
            missing_rate = (
                0 if reading_count == 0 else 1 - geometry_count / reading_count
            )
            result["category_quality"].append(
                {
                    "category": key,
                    "geometry_count": geometry_count,
                    "reading_count": len(value),
                    "missing_rate": missing_rate,
                }
            )

            total_reading += reading_count
            total_geometry += geometry_count
        result["category_quality"].append(
            {
                "category": "Total",
                "geometry_count": total_geometry,
                "reading_count": total_reading,
                "missing_rate": 1 - total_geometry / total_reading,
            }
        )

        result["page_quality"] = self._compute_overlap(layout_info)

        report_file = os.path.join(self.directory, "result/quality_report.json")
        utils.export_to_json(result, report_file)

    def annotate(self):
        layout_info = self.generate_layout_info()
        layout_info_file = os.path.join(self.directory, "result/layout_info.json")
        serialized_layout_info = [
            block.to_dict() for blocks in layout_info.values() for block in blocks
        ]
        utils.export_to_json(serialized_layout_info, layout_info_file)

        image_annotation = self.generate_image_annotation(layout_info)
        reading_annotation = self.generate_reading_annotation(layout_info)
        order_annotation = self.generate_order_annotation(layout_info)

        layout_annotation_file = os.path.join(
            self.directory, "result/layout_annotation.json"
        )
        reading_annotation_file = os.path.join(
            self.directory, "result/reading_annotation.json"
        )
        order_annotation_file = os.path.join(
            self.directory, "result/order_annotation.json"
        )

        utils.export_to_coco(
            layout_info, image_annotation, filename=layout_annotation_file
        )
        utils.export_to_json(reading_annotation, reading_annotation_file)
        utils.export_to_json(order_annotation, order_annotation_file)

        self.generate_quality_report(layout_info)
