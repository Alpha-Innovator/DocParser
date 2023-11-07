from collections import defaultdict
import os
import glob
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
from skimage.measure import label, regionprops
import re
from tqdm import tqdm

from pdfminer.layout import LTComponent
from rendering import envs
from logger import logger
from config import config
from rendering.utils import load_json

log = logger.get_logger(__name__)


def get_image_pairs(dir1: str, dir2: str):
    """
    Generate a list of image pairs based on the directories provided.

    Parameters:
        dir1 (str): The directory path where the first set of images is located.
        dir2 (str): The directory path where the second set of images is located.

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
        match = re.search(r"_(\d+)\.png$", rendered_png_files[i])
        page_index = match.group(1)
        page_indices.append(int(page_index))

    for i in range(len(changed_png_files)):
        match = re.search(r"_(\d+)\.png$", rendered_png_files[i])
        page_index = match.group(1)
        if int(page_index) != page_indices[i]:
            raise FileNotFoundError("Wrong image path or file name or page index!")

    image_pairs = list(zip(page_indices, rendered_png_files, changed_png_files))
    return image_pairs


class LayoutAnnotation:
    def __init__(self, directory: str, layout_metadata: Dict[str, float]) -> None:
        self.directory = directory
        self.background_dir = os.path.join(directory, "white")
        self.env_dirs = self.get_matching_subdirectories()
        self.layout_metadata = self.parse_metadata(layout_metadata)

    def parse_metadata(self, layout_metadata: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: move this to config
        ppi = 72
        ONE_INCH = 72.27
        pt2px = ppi / ONE_INCH
        image_height, pdf_height = 2200, 792
        pdf_width = 612
        px2img = image_height / pdf_height
        textwidth = layout_metadata["textwidth"]
        columnsep = layout_metadata["columnsep"]
        columnwidth = layout_metadata["columnwidth"]

        # textwidth = n * columnwidth + (n - 1) * columnsep
        num_columns = round((textwidth + columnsep) / (columnwidth + columnsep))
        layout_metadata["num_columns"] = num_columns
        # this member stores the boundary for each column,
        # if one column, it is [0, page_width]
        # if two column, it is [0, columnwidth + columnsep / 2, page_width]
        # if three column, it is [0, columnwidth + columnsep / 2,
        # 2 * columnwidth + 3 * columnsep / 2, page_width]
        layout_metadata["separations"] = [0]

        # https://www.overleaf.com/learn/latex/Page_size_and_margins
        element1 = ONE_INCH + layout_metadata["hoffset"]
        element3 = layout_metadata["oddsidemargin"]
        margin_width = element1 + element3

        # x is the left boundary of a column
        x = margin_width - columnsep
        for i in range(num_columns - 1):
            separation = x + columnwidth + columnsep
            layout_metadata["separations"].append(separation * pt2px * px2img)
            x += separation

        layout_metadata["separations"].append(pdf_width * px2img)
        log.debug(f"Separations: {layout_metadata['separations']}")

        return layout_metadata

    def get_matching_subdirectories(self) -> List[str]:
        result = []
        for name in os.listdir(self.directory):
            if not os.path.isdir(os.path.join(self.directory, name)):
                continue
            if not any(name.startswith(prefix) for prefix in envs.complex_env_list):
                continue
            result.append(name)
        return result

    def get_category(self, dir: str):
        dir_name = os.path.basename(dir)
        env_name = None
        for env in envs.complex_env_list:
            if dir_name.startswith(env):
                env_name = env

        if env_name is None:
            raise ValueError(f"Invalid directory name: {dir_name}")

        return config.name2category[env_name]

    def generate(self) -> Tuple[Dict, Dict]:
        # TODO: move this to config
        threshold = 0.3
        geometry_info = defaultdict(list)
        category_info = defaultdict(list)
        for dir_name in tqdm(self.env_dirs):
            env_dir = os.path.join(self.directory, dir_name)
            image_pairs = get_image_pairs(env_dir, self.background_dir)
            category = self.get_category(dir_name)
            for image_pair in image_pairs:
                page_index = image_pair[0]

                image1_array = np.array(plt.imread(image_pair[1]), dtype=np.uint8)
                image2_array = np.array(plt.imread(image_pair[2]), dtype=np.uint8)

                diff_image = np.abs(image2_array - image1_array, dtype=np.uint8)
                labeled_image, num = label(diff_image > threshold, return_num=True)
                log.debug(f"Number of connected components: {num}")

                regions = regionprops(labeled_image)
                bounding_boxes = [region.bbox for region in regions]

                if len(bounding_boxes) == 0:
                    continue

                separations = self.layout_metadata["separations"]
                # We do not consider the cross column tables.
                if config.category2name[category] in [
                    "Table",
                    "Caption",
                    "Algorithm",
                    "Footnote",
                ]:
                    min_x = min(bounding_boxes, key=lambda x: x[1])[1]
                    min_y = min(bounding_boxes, key=lambda x: x[0])[0]
                    max_x = max(bounding_boxes, key=lambda x: x[4])[4]
                    max_y = max(bounding_boxes, key=lambda x: x[3])[3]

                    element = LTComponent(bbox=(min_x, min_y, max_x, max_y))
                    geometry_info[page_index].append(element)
                    category_info[page_index].append(category)
                    continue

                for column in range(self.layout_metadata["num_columns"]):
                    log.debug(
                        f"Processing column {column}, separation: [{separations[column]}: {separations[column + 1]}]"
                    )
                    column_boxes = [
                        bb
                        for bb in bounding_boxes
                        if bb[1] >= separations[column]
                        and bb[4] <= separations[column + 1]
                    ]
                    log.debug(f"Column {column}: {column_boxes}")
                    if not column_boxes:
                        continue
                    min_x = min(column_boxes, key=lambda x: x[1])[1]
                    min_y = min(column_boxes, key=lambda x: x[0])[0]
                    max_x = max(column_boxes, key=lambda x: x[4])[4]
                    max_y = max(column_boxes, key=lambda x: x[3])[3]

                    element = LTComponent(bbox=(min_x, min_y, max_x, max_y))
                    geometry_info[page_index].append(element)
                    category_info[page_index].append(category)

        return geometry_info, category_info


def run(main_directory):
    layout_metadata = load_json(
        os.path.join(main_directory, "result/layout_metadata.json")
    )
    layout_annotation = LayoutAnnotation(main_directory, layout_metadata)
    geometry_info, category_info = layout_annotation.generate()
    return geometry_info, category_info
