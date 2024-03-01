from collections import defaultdict
import os
import glob
from typing import DefaultDict, Dict, List, Tuple
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


class LayoutAnnotation:
    # https://www.overleaf.com/learn/latex/Lengths_in_LaTeX
    ONE_INCH = 72.27

    def __init__(self, main_directory: str) -> None:
        self.main_directory = main_directory
        self.output_directory = os.path.join(main_directory, "output")
        self.result_directory = os.path.join(self.output_directory, "result")
        self.layout_metadata: Dict = {}
        self.text_info = utils.load_json(
            os.path.join(self.result_directory, "texts.json")
        )
        self.pdf_images_path = os.path.join(self.output_directory, "paper_colored")

    def extract_pdf_layouts(self) -> List[LTPage]:
        """Extracts layout information of each page from a rendered PDF.

        This method reads the rendered PDF file and extracts the layout information for each page.
        The layout information includes the position, size, and other attributes of each element on the page.

        Returns:
            List[LTPage]: A list of LTPage objects representing the layout of each page.

        Example:
            >>> renderer = PDFRenderer()
            >>> layouts = renderer.extract_pdf_layouts()
            >>> for layout in layouts:
            ...     print(layout)
            <LTPage(1) width:612.0 height:792.0>
            <LTPage(2) width:612.0 height:792.0>
            ...
        """
        rendered_pdf = os.path.join(self.main_directory, "paper_colored.pdf")
        page_layouts = extract_pages(rendered_pdf)
        return list(page_layouts)

    def parse_metadata(self, pdf_layouts: List[LTPage]) -> None:
        """Parse metadata from PDF layouts and store them in the layout_metadata attribute.

        Args:
        - pdf_layouts (List[LTPage]): A list of LTPage objects representing the PDF layouts.

        Returns:
        - None
        """
        pt2px = config.ppi / self.ONE_INCH

        layout_metadata = dict()

        # get metadata from log file
        log_file = os.path.join(self.main_directory, "paper_colored.log")
        # see renderer.py add_layout_definitions for details
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
        element4 = layout_metadata["topmargin"]
        element5 = layout_metadata["headheight"]
        element6 = layout_metadata["headsep"]
        margin_width = element1 + element3
        margin_height = (element2 - (element4 - element5)) + element6 / 2
        layout_metadata["margin_width"] = margin_width

        # sort all images by page index, see utils.pdf2jpg for details
        image_files = sorted(
            glob.glob(f"{self.pdf_images_path}/*.jpg"), key=lambda x: x[-6:-4]
        )
        for page_index, page_layout in enumerate(pdf_layouts):
            layout_metadata[page_index] = {}

            pdf_width, pdf_height = page_layout.width, page_layout.height
            layout_metadata[page_index]["pdf_width"] = pdf_width
            layout_metadata[page_index]["pdf_height"] = pdf_height

            with Image.open(image_files[page_index]) as page_image:
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
            layout_metadata[page_index]["top_margin"] = margin_height

        utils.export_to_json(
            layout_metadata,
            os.path.join(self.result_directory, "layout_metadata.json"),
        )

        self.layout_metadata = layout_metadata

    def generate_figure_bb(self, pdf_layouts: List[LTPage]) -> Dict[int, List[Block]]:
        """Generate bounding boxes for figures in a PDF layout using Pdfminer.

        Args:
            pdf_layouts (List[LTPage]): A list of LTPage objects representing the layout of a PDF.

        Returns:
            Dict[int, List[Block]]: A dictionary where the keys are page indices and the values are lists of
            Block objects representing the bounding boxes of figures on each page.
        """
        layout_info = defaultdict(list)
        for page_index, page_layout in enumerate(pdf_layouts):
            layout_info[page_index].extend(
                [
                    Block(
                        bounding_box=BoundingBox(*element.bbox),
                        page_index=page_index,
                        category=config.name2category["Figure"],
                        source_code="",  # currently, figure block will have no source code match
                    )
                    for element in page_layout
                    if isinstance(element, LTFigure)
                ]
            )

        # convert bounding boxes from PDF coordinate system to image coordinate system
        self.transform(layout_info)
        return layout_info

    def transform(self, layout_info: Dict[int, List[Block]]) -> None:
        """Transforms bounding boxes from PDF coordinate system to image coordinate system,
        and change them in place.

        Args:
            layout_info (Dict[int, List[Block]]): A dictionary containing the layout information of each page.
                The keys represent the page indices, and the values are lists of Block objects
                representing the elements in the layout.

        Returns:
            None
        """
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
        """Generates non-figure bounding boxes using the image pairs.

        Returns:
            Dict[int, List[Block]]: A dictionary containing the layout information of each page.
                The keys represent the page indices, and the values are lists of Block objects
                representing the elements in the layout.
        """
        background_directory = os.path.join(self.output_directory, "paper_white")
        block_directories = glob.glob(
            f"{self.output_directory}/paper_{config.folder_prefix}*"
        )
        layout_info = defaultdict(list)
        pattern = r"paper_(\w+)_(\d{5})_(.*?)_(\d{5})"

        for block_directory in tqdm(sorted(block_directories)):
            log.debug(f"Processing {block_directory}")
            image_pairs = get_image_pairs(block_directory, background_directory)
            matches = re.match(pattern, os.path.basename(block_directory))
            if not matches:
                raise ValueError(f"Cannot find the matching pattern: {block_directory}")
            category = matches.group(3)
            index = int(matches.group(4))
            log.debug(f"category: {category}, index: {index}")

            elements = []
            for image_pair in image_pairs:
                page_index = image_pair[0]

                image1_array = np.array(plt.imread(image_pair[1]), dtype=np.uint8)
                image2_array = np.array(plt.imread(image_pair[2]), dtype=np.uint8)

                diff_image = np.abs(image2_array - image1_array, dtype=np.uint8)
                if np.all(diff_image == 0):
                    continue
                labeled_image, num = label(
                    diff_image > config.threshold, return_num=True
                )
                if num == 0:
                    continue

                regions = regionprops(labeled_image)
                bounding_boxes = [region.bbox for region in regions]

                if len(bounding_boxes) == 0:
                    continue

                separations = self.layout_metadata[page_index]["separations"]
                top_margin = self.layout_metadata[page_index]["top_margin"]

                # We do not consider the cross column case for these envs.
                if category in envs.one_column_envs:
                    bboxes = [bb for bb in bounding_boxes if bb[0] >= top_margin]
                    if len(bboxes) == 0:
                        continue
                    element = Block(
                        bounding_box=BoundingBox.from_list(bboxes),
                        source_code=self.text_info[category][index],
                        category=config.name2category[category],
                        page_index=page_index,
                    )
                    if elements:
                        element.parent_block = elements[-1].block_id
                    elements.append(element)
                    continue

                # consider possible cross column case
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
                        source_code=self.text_info[category][index],
                        category=config.name2category[category],
                        page_index=page_index,
                    )
                    if elements:
                        element.parent_block = elements[-1].block_id

                    if (
                        len(elements) > 0
                        and elements[-1].category == element.category
                        and elements[-1].page_index == element.page_index
                        and elements[-1].source_code == element.source_code
                        and elements[-1].bbox.overlaps(element.bbox)
                    ):
                        elements[-1].bbox = BoundingBox(
                            min(
                                elements[-1].bbox.x0,
                                element.bbox.x0,
                            ),
                            min(
                                elements[-1].bbox.y0,
                                element.bbox.y0,
                            ),
                            max(
                                elements[-1].bbox.x1,
                                element.bbox.x1,
                            ),
                            max(
                                elements[-1].bbox.y1,
                                element.bbox.y1,
                            ),
                        )
                        continue
                    elements.append(element)

            for element in elements:
                layout_info[element.page_index].append(element)

        return layout_info

    def generate_layout_info(self) -> Dict[int, List[Block]]:
        """Generate layout information for the given PDF.

        This function extracts the PDF layouts using the `extract_pdf_layouts` method
        and parses the metadata using the `parse_metadata` method.
        Then, it generates non-figure bounding boxes using the `generate_non_figure_bb` method
        and figure bounding boxes using the `generate_figure_bb` method.

        Args:
            None

        Returns:
            Dict[int, List[Block]]: A dictionary containing the layout information for
            each page of the PDF.
            The keys represent the page indices, and the values are lists of `Block` objects
            that represent the bounding boxes.

        """
        pdf_layouts = self.extract_pdf_layouts()
        self.parse_metadata(pdf_layouts)
        layout_info = self.generate_non_figure_bb()
        figure_layout_info = self.generate_figure_bb(pdf_layouts)

        for page_index in layout_info.keys():
            layout_info[page_index].extend(figure_layout_info[page_index])
        return layout_info

    def generate_reading_annotation(
        self, layout_info: Dict[int, List[Block]]
    ) -> DefaultDict[str, List]:
        """Generate a reading annotation based on the layout information.

        Args:
            layout_info (Dict[int, List[Block]]): A dictionary containing the layout information
                for each page index. The keys are the page indices and the values are lists of
                `Block` objects representing the blocks on each page.

        Returns:
            DefaultDict[str, List]: A defaultdict containing the reading annotation. The keys
            of the defaultdict are the page indices and the values are lists of dictionaries
            representing the reading annotation for each block on the page. Each dictionary
            contains the following keys:
                - "source_code": The source code of the block.
                - "image_path": The path to the saved image of the block.
                - "category": The category of the block.

            The defaultdict also contains the following keys:
                - "categories": A list of dictionaries representing the categories. Each
                  dictionary contains the following keys:
                      - "id": The ID of the category.
                      - "name": The name of the category.
                - "macros": A dictionary containing the macro definitions extracted from
                  the original tex file.
        """
        reading_annotation = defaultdict(list)

        # sort all images by page index, see utils.pdf2jpg for details
        image_files = sorted(
            glob.glob(os.path.join(self.pdf_images_path, "*.jpg")),
            key=lambda x: x[-6:-4],
        )
        count = 0
        for page_index in layout_info.keys():
            page_image = Image.open(image_files[page_index])
            for block in layout_info[page_index]:
                cropped_image = page_image.crop(block.bbox)

                image_name = config.folder_prefix + str(count).zfill(4) + ".jpg"
                count += 1
                image_path = os.path.join(self.result_directory, image_name)
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

    def generate_image_annotation(
        self, layout_info: Dict[int, List[Block]]
    ) -> Dict[int, str]:
        """Generate image annotations based on the layout information.

        Args:
            layout_info (Dict[int, List[Block]]): A dictionary mapping page indices to a list of Block objects
            representing the layout information.

        Returns:
            Dict[int, str]: A dictionary mapping page indices to annotated image filenames.
        """
        # sort all images by page index, see utils.pdf2jpg for details
        # FIXME: use more robust way
        image_files = sorted(
            glob.glob(os.path.join(self.pdf_images_path, "*.jpg")),
            key=lambda x: x[-6:-4],
        )

        image_info = {}  # annotation image info member of COCO
        for page_index in layout_info.keys():
            page_image = Image.open(image_files[page_index])
            draw = ImageDraw.Draw(page_image)
            # use `locate .ttf` to find the available fonts
            font = ImageFont.truetype(
                config.config["annotation_image_font_type"],
                config.config["annotation_image_font_size"],
            )

            for element in layout_info[page_index]:
                category = element.category
                draw.rectangle(
                    element.bbox, outline=config.colors_map[str(category)], width=3
                )
                draw.text(
                    (element.bbox[0], element.bbox[1]),
                    config.category2name[category],
                    fill=(255, 0, 0),
                    font=font,
                )

            image_name = "page_" + str(page_index).zfill(4) + ".jpg"
            annotated_image_path = os.path.join(self.result_directory, image_name)
            image_info[page_index] = image_name
            page_image.save(annotated_image_path)
            page_image.close()

        return image_info

    def _compute_overlap(self, layout_info: Dict[int, List[Block]]) -> List[Dict]:
        """Computes the overlap between blocks in a layout.

        Args:
            layout_info (Dict[int, List[Block]]): A dictionary where the keys are page indices
                and the values are lists of blocks on each page.

        Returns:
            List[Dict]: A list of dictionaries containing the overlap information for each page and
                        the total overlap information.

        """
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

    def generate_quality_report(self, layout_info: Dict[int, List[Block]]) -> None:
        """Generates a quality report based on the provided layout information.

        Args:
            layout_info (Dict[int, List[Block]]): A dictionary where the keys are page indices
                and the values are lists of blocks on each page.

        Returns:
            None
        """
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

        report_file = os.path.join(self.result_directory, "quality_report.json")
        utils.export_to_json(result, report_file)

    def annotate(self):
        """Annotates the layout, reading, order, and quality report of the given image.

        Returns:
            None
        """
        # step1: generate layout info
        layout_info = self.generate_layout_info()

        # step2: generate layout detection result
        image_annotation = self.generate_image_annotation(layout_info)
        layout_annotation_file = os.path.join(
            self.result_directory, "layout_annotation.json"
        )
        utils.export_to_coco(
            layout_info, image_annotation, filename=layout_annotation_file
        )

        # step3: generate reading annotation
        reading_annotation = self.generate_reading_annotation(layout_info)
        reading_annotation_file = os.path.join(
            self.result_directory, "reading_annotation.json"
        )
        utils.export_to_json(reading_annotation, reading_annotation_file)

        # step4: generate order annotation
        vrdu_order_annotation = OrderAnnotation(layout_info)
        order_annotation = vrdu_order_annotation.annotate()

        order_annotation_file = os.path.join(
            self.result_directory, "order_annotation.json"
        )

        utils.export_to_json(order_annotation, order_annotation_file)

        # step5: generate quality report
        self.generate_quality_report(layout_info)


class OrderAnnotation:
    def __init__(self, layout_info) -> None:
        self.layout_info = layout_info

    def annotate(self):
        annotations = {}

        annotations["orders"] = []
        sortable_annotations = self.generate_sortable_envs_order()
        annotations["orders"].extend(sortable_annotations)
        float_annotations = self.generate_float_envs_order()
        annotations["orders"].extend(float_annotations)
        cross_reference_annotation = self.generate_cross_reference_order()
        annotations["orders"].extend(cross_reference_annotation)
        return annotations

    def generate_cross_reference_order(self):
        # TODO: complete this
        # parse label in texts
        # ref to label
        pass
        return []

    def generate_float_envs_order(self):
        # TODO: complete this
        # caption to env
        # label to env
        pass
        # 1. caption-env attach, implicit cite and add label
        # 2. equation-label attach, add label
        return []

    def generate_sortable_envs_order(self):
        stack = []
        annotations = []
        relation_map = config.relation_map
        sortable_category = [
            config.name2category[name] for name in config.sortable_envs
        ]

        sortable_elements = [
            _block
            for page_index in self.layout_info.keys()
            for _block in self.layout_info[page_index]
            if _block.category in sortable_category
        ]

        # TODO: move this to config
        peer_title_categories = [
            config.name2category[x] for x in ["Title", "PaperTitle", "Abstract"]
        ]

        peer_text_categories = [
            config.name2category[x] for x in ["Text", "Text-EQ", "Equation", "List"]
        ]

        for index, element in enumerate(sortable_elements):
            if index == 0:
                stack.append(element)
                continue

            if element.category in peer_title_categories:
                while stack and stack[-1].category not in peer_title_categories:
                    stack.pop()

                # no peer categories
                if not stack:
                    stack.append(element)
                    continue

                # not in the same category, label it as peer relationship
                # or in the same category but the category is not Title
                if (
                    element.category != stack[-1].category
                    or element.category == config.name2category["Title"]
                ):
                    annotations.append(
                        {
                            "type": "peer",
                            "from": element.block_id,
                            "to": stack[-1].block_id,
                        }
                    )
                    stack.append(element)
                    continue

                # both are in the Title category
                cur_title = utils.extract_title_name(element.source_code)
                while (
                    stack
                    and (cur_title, utils.extract_title_name(stack[-1].source_code))
                    not in config.relation_map
                ):
                    stack.pop()

                # no relation found
                if not stack:
                    stack.append(element)
                    continue

                # determine the relation in Title category
                prev_title = utils.extract_title_name(stack[-1].source_code)
                annotations.append(
                    {
                        "type": config.relation_map[(cur_title, prev_title)],
                        "from": element.block_id,
                        "to": stack[-1].block_id,
                    }
                )
                stack.append(element)
            elif element.category == config.name2category["Footnote"]:
                # FIXME: this may happens when PaperTitle is not parsed and authors is represented as Footnote
                if not stack:
                    continue

                annotations.append(
                    {
                        "type": "inline",
                        "from": element.block_id,
                        "to": stack[-1].block_id,
                    }
                )
                # the footnote element is not appended to the stack due to inline relationship is a container

            elif element.category in peer_text_categories:
                cur_name = config.category2name[element.category]
                prev_name = config.category2name[stack[-1].category]
                annotations.append(
                    {
                        "type": relation_map.get(
                            (cur_name, prev_name),
                            "Unknown",
                        ),
                        "from": element.block_id,
                        "to": stack[-1].block_id,
                    }
                )
                stack.append(element)

            else:
                raise ValueError(f"Unsupported category {element.category}")

        return annotations


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
    file_pattern = os.path.join(dir1, "*.jpg")
    rendered_jpg_files = sorted(glob.glob(file_pattern))
    file_pattern = os.path.join(dir2, "*.jpg")
    changed_jpg_files = sorted(glob.glob(file_pattern))

    if len(rendered_jpg_files) != len(changed_jpg_files):
        raise FileNotFoundError("Wrong image path or file name or page index!")

    def extract_page_index(filename: str) -> int:
        pattern = r"thread-\d+-page-(\d+)\.jpg"

        match = re.search(pattern, filename)
        if match:
            page_index = int(match.group(1))
            return page_index - 1
        else:
            raise ValueError("Cannot found corresponding page index")

    page_indices = []
    for i in range(len(rendered_jpg_files)):
        file_name = os.path.basename(rendered_jpg_files[i])
        page_index = extract_page_index(file_name)
        page_indices.append(int(page_index))

    image_pairs = list(zip(page_indices, rendered_jpg_files, changed_jpg_files))
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
