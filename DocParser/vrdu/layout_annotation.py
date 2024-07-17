from collections import defaultdict
import os
import glob
import subprocess
from typing import Any, DefaultDict, Dict, List
import matplotlib.pyplot as plt
import numpy as np
from skimage.measure import label, regionprops
from PIL import Image, ImageDraw, ImageFont
import re
from tqdm import tqdm

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTPage


from DocParser.vrdu import utils
from DocParser.vrdu.block import Block, BoundingBox
from DocParser.vrdu.config import config, envs
from DocParser.vrdu import logger

log = logger.get_logger(__name__)


class LayoutAnnotation:
    # https://www.overleaf.com/learn/latex/Lengths_in_LaTeX
    ONE_INCH = 72.27

    def __init__(self, tex_file: str) -> None:
        self.tex_file = tex_file
        self.main_directory = os.path.dirname(tex_file)
        self.output_directory = os.path.join(self.main_directory, "output")
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

    def retrieve_figure_source_code(
        self, figure_layout_info: Dict[int, List[Block]]
    ) -> None:
        """Retrieves the source code of a figure using synctex.

        Args:
            figure_layout_info (Dict[int, List[Block]]): A dictionary where the keys are page indices
                and the values are lists of Block objects representing the bounding boxes of figures on each page.

        Returns:
            None

        Note:
            use `synctex help edit` to view usage of synctex
        """
        # paper_colored.tex is what we are working for
        tex_filename = os.path.basename(self.tex_file).replace(
            "paper_original", "paper_colored"
        )
        pdf_filename = tex_filename.replace(".tex", ".pdf")
        with open(os.path.join(self.main_directory, tex_filename), "r") as file:
            content_lines = file.readlines()

        for page_index, blocks in figure_layout_info.items():
            for block in blocks:
                bbox = block.bbox
                center_x, center_y = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
                log.debug(
                    f"page index: {page_index + 1}, center: ({center_x}, {center_y}), pdf filename: {pdf_filename}"
                )
                # use synctex to retrieve the line index corresponding to the center of the bounding box
                result = subprocess.run(
                    [
                        "synctex",
                        "edit",
                        "-o",
                        f"{page_index + 1}:{center_x:.2f}:{center_y:.2f}:{pdf_filename}",
                        "-d",
                        self.main_directory,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                # parse the output of synctex to get the source code
                line_index = result.stdout.split("\nLine:")[1].split("\n")[0]
                block.source_code = content_lines[int(line_index) - 1]
                log.debug(f"line index: {line_index}, source code: {block.source_code}")

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
            height = page_layout.height
            for element in page_layout:
                if not isinstance(element, LTFigure):
                    continue
                # the coordinate system of Pdfminer is in contrast to the coordinate system of the image
                # by flipping the y axis
                y0 = height - element.bbox[3]
                y1 = height - element.bbox[1]
                x0 = element.bbox[0]
                x1 = element.bbox[2]
                layout_info[page_index].append(
                    Block(
                        bounding_box=BoundingBox(x0, y0, x1, y1),
                        page_index=page_index,
                        category=config.name2category["Figure"],
                        source_code="",
                    )
                )

        # find the corresponding source code to figure bounding box
        self.retrieve_figure_source_code(layout_info)

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
            px2img = self.layout_metadata[page_index]["px2img"]
            for index, element in enumerate(layout_info[page_index]):
                x0, y0, x1, y1 = element.bbox
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
                    bounding_boxes = [bb for bb in bounding_boxes]
                    if len(bounding_boxes) == 0:
                        continue
                    element = Block(
                        bounding_box=BoundingBox.from_list(bounding_boxes),
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
                        and elements[-1].bbox.overlap(element.bbox)
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

    def generate_image_annotation(
        self, layout_info: Dict[int, List[Block]]
    ) -> Dict[int, Dict[str, Any]]:
        """Generate image annotations based on the layout information.

        Args:
            layout_info (Dict[int, List[Block]]): A dictionary mapping page indices to a list of Block objects
            representing the layout information.

        Returns:
            Dict[int, Dict[str, Any]]: A dictionary mapping page indices to annotated image info.
        """
        # sort all images by page index, see utils.pdf2jpg for details
        # FIXME: use more robust way
        image_files = sorted(
            glob.glob(os.path.join(self.pdf_images_path, "*.jpg")),
            key=lambda x: x[-6:-4],
        )

        image_info = {}  # annotation image info member of COCO
        for page_index in layout_info.keys():
            image_info[page_index] = {}
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
                    element.bbox.to_tuple(),
                    outline=config.colors_map[str(category)],
                    width=3,
                )
                draw.text(
                    (element.bbox[0], element.bbox[1]),
                    config.category2name[category],
                    fill=(255, 0, 0),
                    font=font,
                )

            image_name = "page_" + str(page_index).zfill(4) + ".jpg"
            annotated_image_path = os.path.join(self.result_directory, image_name)
            image_info[page_index]["file_name"] = image_name
            image_info[page_index]["width"] = page_image.width
            image_info[page_index]["height"] = page_image.height
            page_image.save(annotated_image_path)
            page_image.close()

        return image_info

    def annotate(self):
        """Annotates the layout, reading, order, and quality report of the given image.

        Returns:
            None
        """
        # step1: generate layout info
        layout_info = self.generate_layout_info()
        layout_info_data = {
            key: [x.to_dict() for x in values] for key, values in layout_info.items()
        }
        layout_info_file = os.path.join(self.result_directory, "layout_info.json")
        utils.export_to_json(layout_info_data, layout_info_file)

        # step2: generate layout detection result
        image_annotation = self.generate_image_annotation(layout_info)
        layout_annotation_file = os.path.join(
            self.result_directory, "layout_annotation.json"
        )
        utils.export_to_coco(
            layout_info, image_annotation, file_path=layout_annotation_file
        )


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
        draw.rectangle(
            element.bbox.to_tuple(), outline=config.colors_map[str(category)], width=3
        )
        draw.text(
            (element.bbox[0], element.bbox[1]),
            config.category2name[category],
            fill=(255, 0, 0),
            font=font,
        )

    return page_image
