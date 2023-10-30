import json
import os
from typing import Dict, List
import datetime
import argparse
from PIL import Image, ImageDraw, ImageFont


from annotation.layout import geometry
from pdfminer.layout import LTPage, LTComponent
from logger import logger
from config import config

from annotation.layout import generate_simple_env_bb
from annotation.layout import generate_complex_env_bb

log = logger.setup_app_level_logger(file_name="app_debug.log", mode="a")


def merge_env_bboxes(elements: List[LTComponent], ratio=1.0) -> List[LTComponent]:
    elements.sort(key=lambda x: x.bbox[1])
    result = []

    for element in elements:
        x0, y0, x1, y1 = element.bbox
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        height = y1 - y0
        width = x1 - x0

        has_been_merged = False
        for item in result:
            if geometry.inside_bb(element, item):
                continue
            item_center_x = (item.bbox[0] + item.bbox[2]) / 2
            item_center_y = (item.bbox[1] + item.bbox[3]) / 2
            if (
                abs(center_y - item_center_y) <= ratio * height
                and abs(center_x - item_center_x) <= 0.5 * width
            ):
                item.bbox = (
                    min(x0, item.bbox[0]),
                    min(y0, item.bbox[1]),
                    max(x1, item.bbox[2]),
                    max(y1, item.bbox[3]),
                )
                has_been_merged = True
                break

        if not has_been_merged:
            result.append(element)

    return result


def export_to_coco(
    file_elements: Dict[int, List[LTComponent]],
    image_infos: Dict[int, str],
    category_infos: Dict[int, Dict[int, int]],
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
    for page_index, page_elements in file_elements.items():
        for index, element in enumerate(page_elements):
            if isinstance(element, LTPage):
                image = {
                    "id": page_index,
                    "width": element.bbox[2] - element.bbox[0],
                    "height": element.bbox[3] - element.bbox[1],
                    "file_name": image_infos[page_index],
                    "coco_url": "",  # TODO: modify this
                    "date_captured": "",  # TODO: modify this
                    "flickr_url": "",  # TODO: modify this
                    "license": 0,  # TODO: modify this
                }
                result["images"].append(image)
            else:
                width = element.bbox[2] - element.bbox[0]
                height = element.bbox[3] - element.bbox[1]
                annotation = {
                    "id": index,
                    "image_id": page_index,
                    "category_id": category_infos[page_index][index],
                    "segmentation": [],
                    "bbox": [element.bbox[0], element.bbox[1], width, height],
                    "area": width * height,
                    "iscrowd": 0,
                }
                result["annotations"].append(annotation)

    with open(filename, "w") as f:
        json.dump(result, f)


def merge_info(
    geometry_info, geometry_info_complex, category_info, category_info_complex
):
    # TODO: post process
    for page_index, complex_elements in geometry_info_complex.items():
        for complex_element in complex_elements:
            for index, element in enumerate(geometry_info[page_index]):
                if isinstance(element, LTPage):
                    continue

                x0, y0, x1, y1 = complex_element.bbox
                x2, y2, x3, y3 = element.bbox

                if geometry.inside_bb(complex_element, element):
                    # TODO: delete bbox is it is empty
                    element.bbox = (x2, y2, x3, y0)
                    geometry_info[page_index].append(LTComponent(bbox=(x2, y1, x3, y3)))
                    category_info[page_index].append(category_info[page_index][index])
                    break
                
                # FIXME: still have bugs
                if geometry.intersects_bb(complex_element, element):
                    # shrink up
                    if y0 <= y3 <= y1:
                        element.bbox = (x2, y2, x3, y0)
                        break
                    # shrink down
                    if y0 <= y2 <= y1:
                        element.bbox = (x2, y1, x3, y3)
                        break

        geometry_info[page_index].extend(geometry_info_complex[page_index])
        category_info[page_index].extend(category_info_complex[page_index])
    return geometry_info, category_info


def merge_category_info(info, info_complex):
    for page_index, page_elements in info.items():
        info[page_index].extend(info_complex[page_index])
    return info


def generate_geometry_annotation(
    page_image: Image.Image,
    page_elements: List[LTComponent],
    category_info: Dict[int, int],
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

    for index, element in enumerate(page_elements):
        category = category_info[index]
        draw.rectangle(element.bbox, outline="red")
        draw.text(
            (element.bbox[0], element.bbox[1]),
            config.category2name[category],
            fill=(255, 0, 0),
            font=font,
        )

    return page_image


def generate_image_info(filename, main_directory, geometry_info, category_info):
    rendered_path = os.path.join(main_directory, "colored")
    result_path = os.path.join(main_directory, "result")
    image_info = {}  # annotation image info member of COCO
    for page_index in geometry_info.keys():
        page_image_path = os.path.join(
            rendered_path, f"{filename}_rendered_colored_page_{page_index}.png"
        )
        page_image = Image.open(page_image_path)
        annotated_image = generate_geometry_annotation(
            page_image,
            geometry_info[page_index],
            category_info[page_index],
        )
        image_name = f"{filename}_annotation_page_{page_index}.png"
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
    parser.add_argument(
        "--file_name", type=str, required=True, help="The name of the file"
    )
    args = parser.parse_args()
    main_directory = args.path
    file_name = args.file_name

    return main_directory, file_name


def main():
    main_directory, file_name = parse_arguments()

    geometry_info, category_info = generate_simple_env_bb.run(main_directory, file_name)

    geometry_info_complex, category_info_complex = generate_complex_env_bb.run(
        main_directory
    )

    geometry_info, category_info = merge_info(
        geometry_info, geometry_info_complex, category_info, category_info_complex
    )
    # category_info = merge_category_info(category_info, category_info_complex)

    image_info = generate_image_info(
        file_name, main_directory, geometry_info, category_info
    )

    json_file = os.path.join(main_directory, "result/layout_annotation.json")
    export_to_coco(geometry_info, image_info, category_info, filename=json_file)


if __name__ == "__main__":
    main()
