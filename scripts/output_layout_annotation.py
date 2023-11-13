from collections import defaultdict
import json
import os
from typing import Dict, List
import datetime
import argparse
from PIL import Image, ImageDraw, ImageFont


from logger import logger
from config import config

from annotation.reading.block import Block
from annotation.layout import generate_simple_env_bb
from annotation.layout import generate_complex_env_bb
from rendering.utils import export_to_json

log = logger.setup_app_level_logger(file_name="app_debug.log", mode="a")


def export_to_coco(
    layout_info: Dict,
    image_infos: Dict[int, str],
    filename: str,
) -> None:
    result = {
        "info": {
            "year": 2023,
            "version": "1.0",
            "description": "Visually Rich Document Understanding data process",
            "contributor": "manual",
            "url": "https://github.com/MaoSong2022/vrdu_data_process",
            "date_created": f"{datetime.datetime.now()}",
        },
        "licenses": [  # TODO: modify this
            {
                "url": "http://creativecommons.org/licenses/by/2.0/",
                "id": 4,
                "name": "Attribution License",
            }
        ],
        "images": [],
        "annotations": [],
        "categories": [
            {"id": index, "name": category}
            for index, category in config.config["category_name"]
        ],
    }

    for page_index, page_elements in layout_info.items():
        page_layout = page_elements[0]
        image = {
            "id": page_index,
            "width": page_layout.width,
            "height": page_layout.height,
            "file_name": image_infos[page_index],
            "coco_url": "",  # TODO: modify this
            "date_captured": "",  # TODO: modify this
            "flickr_url": "",  # TODO: modify this
            "license": 0,  # TODO: modify this
        }
        result["images"].append(image)

        for index, element in enumerate(page_elements[1:]):
            width, height = element.width, element.height
            annotation = {
                "id": index,
                "image_id": page_index,
                "category_id": element.category,
                "segmentation": [],
                "bbox": [element.bbox[0], element.bbox[1], width, height],
                "area": width * height,
                "iscrowd": 0,
            }
            result["annotations"].append(annotation)

    with open(filename, "w") as f:
        json.dump(result, f)


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


def generate_image_info(path, layout_info):
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


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path", type=str, required=True, help="The path to the main directory"
    )
    args = parser.parse_args()
    path = args.path

    return path


def output_reading_annotation(path: str, layout_info: Dict[int, List[Block]]):
    rendered_path = os.path.join(path, "colored")
    result_path = os.path.join(path, "result")
    reading_annotation = defaultdict(list)
    for page_index in layout_info.keys():
        # wrong images
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


def main(path):
    output_path = os.path.join(path, "output")
    simple_layout_info = generate_simple_env_bb.run(output_path)

    # geometry_info, category_info = generate_complex_env_bb.run(path)
    layout_info = generate_complex_env_bb.run(output_path)

    for page_index in layout_info.keys():
        layout_info[page_index].extend(simple_layout_info[page_index])

    image_info = generate_image_info(output_path, layout_info)

    json_file = os.path.join(output_path, "result/layout_annotation.json")
    export_to_coco(layout_info, image_info, filename=json_file)

    reading_annotation = output_reading_annotation(output_path, layout_info)
    export_to_json(reading_annotation, os.path.join(output_path, "result/reading_annotation.json"))

    result = {
        key: [block.to_dict() for block in value] for key, value in layout_info.items()
    }

    export_to_json(result, os.path.join(output_path, "result/layout.json"))


if __name__ == "__main__":
    path = parse_arguments()
    main(path)
