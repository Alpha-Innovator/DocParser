from collections import defaultdict
import glob
import subprocess
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
from skimage.measure import label, regionprops
from PIL import Image, ImageDraw, ImageFont
import re
from tqdm import tqdm
from pathlib import Path

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTFigure, LTPage

from DocParser.vrdu import utils
from DocParser.vrdu.block import Block, BoundingBox
from DocParser.vrdu.config import config, envs


class LayoutAnnotation:
    """Class for extracting and annotating layout information from LaTeX documents."""

    ONE_INCH = 72.27  # LaTeX point unit conversion

    def __init__(self, tex_file: Path) -> None:
        """Initialize LayoutAnnotation with paths and load required data.

        Args:
            tex_file: Path to the LaTeX source file
        """
        self.tex_file = tex_file
        self.main_directory = tex_file.parent
        self.output_directory = self.main_directory / "output"
        self.result_directory = self.output_directory / "result"
        self.pdf_images_path = self.output_directory / "paper_colored"

        # Load text information
        self.text_info = utils.load_json(self.result_directory / "texts.json")
        self.layout_metadata: Dict = {}

    def extract_pdf_layouts(self) -> List[LTPage]:
        """Extract layout information from rendered PDF.

        Returns:
            List of page layout objects
        """
        rendered_pdf = self.main_directory / "paper_colored.pdf"
        return list(extract_pages(rendered_pdf))

    def _parse_log_metadata(self, log_file: Path) -> Dict:
        """Parse LaTeX log file for layout metadata.

        Args:
            log_file: Path to LaTeX log file

        Returns:
            Dictionary of extracted metadata values
        """
        metadata = {}
        pattern = r"\[vrdu_data_process: The (.*) is: ([-+]?\d+\.\d+)pt\]"

        with open(log_file, "r", encoding="latin-1") as f:
            for match in re.findall(pattern, f.read()):
                key, value = match[0], float(match[1])
                metadata[key] = value

        # Calculate number of columns
        textwidth = metadata["textwidth"]
        columnsep = metadata["columnsep"]
        columnwidth = metadata["columnwidth"]
        metadata["num_columns"] = round(
            (textwidth + columnsep) / (columnwidth + columnsep)
        )

        return metadata

    def _calculate_margins(self, metadata: Dict) -> Tuple[float, float]:
        """Calculate page margins from metadata.

        Args:
            metadata: Dictionary of layout metadata

        Returns:
            Tuple of (margin_width, margin_height)
        """
        margin_width = (self.ONE_INCH + metadata["hoffset"]) + metadata["oddsidemargin"]

        margin_height = (
            (self.ONE_INCH + metadata["voffset"])
            - (metadata["topmargin"] - metadata["headheight"])
        ) + metadata["headsep"] / 2

        return margin_width, margin_height

    def parse_metadata(self, pdf_layouts: List[LTPage]) -> None:
        """Parse and store layout metadata from PDF and log file.

        Args:
            pdf_layouts: List of PDF page layouts
        """
        pt2px = config.ppi / self.ONE_INCH
        log_file = self.main_directory / "paper_colored.log"

        # Parse basic metadata
        metadata = self._parse_log_metadata(log_file)
        margin_width, margin_height = self._calculate_margins(metadata)
        metadata["margin_width"] = margin_width

        # Get image files sorted by page number
        image_files = sorted(
            glob.glob(str(self.pdf_images_path / "*.jpg")), key=lambda x: x[-6:-4]
        )

        # Process each page
        for page_idx, page_layout in enumerate(pdf_layouts):
            page_metadata = {
                "pdf_width": page_layout.width,
                "pdf_height": page_layout.height,
                "top_margin": margin_height,
            }

            # Get image dimensions
            with Image.open(image_files[page_idx]) as img:
                page_metadata["image_width"], page_metadata["image_height"] = img.size

            # Calculate scale factors
            px2img = page_metadata["image_height"] / page_layout.height
            page_metadata["px2img"] = px2img

            # Calculate column separations
            separations = [0]
            x = margin_width - 0.5 * metadata["columnsep"]
            for _ in range(metadata["num_columns"] - 1):
                sep = x + metadata["columnwidth"] + metadata["columnsep"]
                separations.append(sep * pt2px * px2img)
                x += sep
            separations.append(page_layout.width * px2img)
            page_metadata["separations"] = separations

            metadata[page_idx] = page_metadata

        self.layout_metadata = metadata
        utils.export_to_json(metadata, self.result_directory / "layout_metadata.json")

    def retrieve_figure_source_code(
        self, figure_layout_info: Dict[int, List[Block]]
    ) -> None:
        """Retrieve LaTeX source code for figures using synctex.

        Args:
            figure_layout_info: Dictionary mapping page numbers to figure blocks
        """
        tex_filename = self.tex_file.name.replace("paper_original", "paper_colored")
        pdf_filename = tex_filename.replace(".tex", ".pdf")

        with open(self.main_directory / tex_filename, "r") as f:
            content_lines = f.readlines()

        for page_idx, blocks in figure_layout_info.items():
            for block in blocks:
                # Get center point of figure
                center_x = (block.bbox[0] + block.bbox[2]) / 2
                center_y = (block.bbox[1] + block.bbox[3]) / 2

                # Run synctex to get source line
                result = subprocess.run(
                    [
                        "synctex",
                        "edit",
                        "-o",
                        f"{page_idx + 1}:{center_x:.2f}:{center_y:.2f}:{pdf_filename}",
                        "-d",
                        str(self.main_directory),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Extract line number and source
                line_idx = int(result.stdout.split("\nLine:")[1].split("\n")[0])
                block.source_code = content_lines[line_idx - 1]

    def generate_figure_bb(self, pdf_layouts: List[LTPage]) -> Dict[int, List[Block]]:
        """Generate bounding boxes for figures in PDF layout.

        Args:
            pdf_layouts: List of PDF page layouts

        Returns:
            Dictionary mapping page numbers to figure blocks
        """
        layout_info = defaultdict(list)

        for page_idx, page in enumerate(pdf_layouts):
            for element in page:
                if not isinstance(element, LTFigure):
                    continue

                # Convert coordinates (flip y-axis)
                y0 = page.height - element.bbox[3]
                y1 = page.height - element.bbox[1]
                x0, x1 = element.bbox[0], element.bbox[2]

                layout_info[page_idx].append(
                    Block(
                        bounding_box=BoundingBox(x0, y0, x1, y1),
                        page_index=page_idx,
                        category=config.name2category["Figure"],
                        source_code="",
                    )
                )

        self.retrieve_figure_source_code(layout_info)
        self.transform(layout_info)
        return layout_info

    def transform(self, layout_info: Dict[int, List[Block]]) -> None:
        """Transform bounding boxes from PDF to image coordinates.

        Args:
            layout_info: Dictionary mapping page numbers to blocks
        """
        for page_idx, elements in layout_info.items():
            px2img = self.layout_metadata[page_idx]["px2img"]

            for element in elements:
                x0, y0, x1, y1 = element.bbox
                width = element.width
                height = element.height

                # Scale coordinates
                x0 *= px2img
                y0 *= px2img
                x1 = x0 + width * px2img
                y1 = y0 + height * px2img

                element.bbox = BoundingBox(x0, y0, x1, y1)

    def _process_bounding_boxes(
        self,
        bounding_boxes: List[Tuple],
        category: str,
        page_idx: int,
        source_code: str,
        elements: List[Block],
    ) -> List[Block]:
        """Process and create blocks for bounding boxes.

        Args:
            bounding_boxes: List of bounding box coordinates
            category: Block category
            page_idx: Page number
            source_code: Source code for block
            elements: Existing block elements

        Returns:
            Updated list of block elements
        """
        separations = self.layout_metadata[page_idx]["separations"]

        if category in envs.one_column_envs:
            if bounding_boxes:
                element = Block(
                    bounding_box=BoundingBox.from_list(bounding_boxes),
                    source_code=source_code,
                    category=config.name2category[category],
                    page_index=page_idx,
                )
                if elements:
                    element.parent_block = elements[-1].block_id
                elements.append(element)
            return elements

        # Handle multi-column case
        for col in range(self.layout_metadata["num_columns"]):
            col_boxes = [
                bb
                for bb in bounding_boxes
                if separations[col] <= bb[1] <= separations[col + 1]
            ]
            if not col_boxes:
                continue

            element = Block(
                bounding_box=BoundingBox.from_list(col_boxes),
                source_code=source_code,
                category=config.name2category[category],
                page_index=page_idx,
            )

            if elements:
                element.parent_block = elements[-1].block_id

            # Merge overlapping blocks
            if (
                elements
                and elements[-1].category == element.category
                and elements[-1].page_index == page_idx
                and elements[-1].source_code == source_code
                and elements[-1].bbox.overlap(element.bbox)
            ):

                elements[-1].bbox = BoundingBox(
                    min(elements[-1].bbox.x0, element.bbox.x0),
                    min(elements[-1].bbox.y0, element.bbox.y0),
                    max(elements[-1].bbox.x1, element.bbox.x1),
                    max(elements[-1].bbox.y1, element.bbox.y1),
                )
            else:
                elements.append(element)

        return elements

    def generate_non_figure_bb(self) -> Dict[int, List[Block]]:
        """Generate bounding boxes for non-figure elements.

        Returns:
            Dictionary mapping page numbers to block elements
        """
        background_dir = self.output_directory / "paper_white"
        block_dirs = glob.glob(
            str(self.output_directory / f"paper_{config.folder_prefix}*")
        )
        layout_info = defaultdict(list)
        pattern = r"paper_(\w+)_(\d{5})_(.*?)_(\d{5})"

        for block_dir in tqdm(sorted(block_dirs)):
            matches = re.match(pattern, Path(block_dir).name)
            if not matches:
                raise ValueError(f"Invalid directory name pattern: {block_dir}")

            category = matches.group(3)
            index = int(matches.group(4))
            elements: List[Block] = []

            for page_idx, img1_path, img2_path in get_image_pairs(
                Path(block_dir), background_dir
            ):
                # Compare images
                img1 = np.array(plt.imread(img1_path), dtype=np.uint8)
                img2 = np.array(plt.imread(img2_path), dtype=np.uint8)
                diff = np.abs(img2 - img1, dtype=np.uint8)

                if np.all(diff == 0):
                    continue

                # Get regions
                labeled, num = label(diff > config.threshold, return_num=True)
                if num == 0:
                    continue

                bounding_boxes = [region.bbox for region in regionprops(labeled)]
                if not bounding_boxes:
                    continue

                elements = self._process_bounding_boxes(
                    bounding_boxes,
                    category,
                    page_idx,
                    self.text_info[category][index],
                    elements,
                )

            for element in elements:
                layout_info[element.page_index].append(element)

        return layout_info

    def generate_layout_info(self) -> Dict[int, List[Block]]:
        """Generate complete layout information.

        Returns:
            Dictionary mapping page numbers to all block elements
        """
        pdf_layouts = self.extract_pdf_layouts()
        self.parse_metadata(pdf_layouts)

        layout_info = self.generate_non_figure_bb()
        figure_layout_info = self.generate_figure_bb(pdf_layouts)

        # Combine figure and non-figure info
        for page_idx, figures in figure_layout_info.items():
            layout_info[page_idx].extend(figures)

        return layout_info

    def generate_image_annotation(
        self, layout_info: Dict[int, List[Block]]
    ) -> Dict[int, Dict[str, Any]]:
        """Generate annotated images with bounding boxes.

        Args:
            layout_info: Dictionary mapping page numbers to blocks

        Returns:
            Dictionary of image annotation information
        """
        image_files = sorted(
            glob.glob(str(self.pdf_images_path / "*.jpg")),
            key=lambda x: x[-6:-4],
        )

        image_info = {}
        for page_idx in layout_info:
            with Image.open(image_files[page_idx]) as page_image:
                annotated = generate_geometry_annotation(
                    page_image, layout_info[page_idx]
                )

                image_name = f"page_{str(page_idx).zfill(4)}.jpg"
                annotated.save(self.result_directory / image_name)

                image_info[page_idx] = {
                    "file_name": image_name,
                    "width": page_image.width,
                    "height": page_image.height,
                }

        return image_info

    def annotate(self):
        """Generate complete layout annotation."""
        # Generate layout information
        layout_info = self.generate_layout_info()
        layout_info_data = {
            key: [x.to_dict() for x in blocks] for key, blocks in layout_info.items()
        }
        utils.export_to_json(
            layout_info_data, self.result_directory / "layout_info.json"
        )

        # Generate annotations
        image_annotation = self.generate_image_annotation(layout_info)
        utils.export_to_coco(
            layout_info,
            image_annotation,
            self.result_directory / "layout_annotation.json",
        )


def get_image_pairs(dir1: Path, dir2: Path) -> List[Tuple[int, str, str]]:
    """Get matching pairs of images from two directories.

    Args:
        dir1: First directory path
        dir2: Second directory path

    Returns:
        List of tuples containing (page_index, image1_path, image2_path)

    Raises:
        FileNotFoundError: If image counts don't match
        ValueError: If page index can't be extracted
    """
    rendered_files = sorted(glob.glob(str(dir1 / "*.jpg")))
    changed_files = sorted(glob.glob(str(dir2 / "*.jpg")))

    if len(rendered_files) != len(changed_files):
        raise FileNotFoundError("Mismatched image counts between directories")

    def extract_page_index(filename: str) -> int:
        match = re.search(r"thread-\d+-page-(\d+)\.jpg", filename)
        if not match:
            raise ValueError(f"Cannot extract page index from {filename}")
        return int(match.group(1)) - 1

    page_indices = [extract_page_index(Path(f).name) for f in rendered_files]
    return list(zip(page_indices, rendered_files, changed_files))


def generate_geometry_annotation(
    page_image: Image.Image, layout_elements: List[Block]
) -> Image.Image:
    """Add geometric annotations to an image.

    Args:
        page_image: Image to annotate
        layout_elements: List of block elements to annotate

    Returns:
        Annotated image
    """
    draw = ImageDraw.Draw(page_image)
    font = ImageFont.truetype(
        config.config["annotation_image_font_type"],
        config.config["annotation_image_font_size"],
    )

    for element in layout_elements:
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
