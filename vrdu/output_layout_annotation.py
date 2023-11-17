import os
import argparse

from vrdu import utils
from vrdu import logger
from vrdu import annotation

log = logger.setup_app_level_logger(file_name="app_debug.log", mode="a")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path", type=str, required=True, help="The path to the main directory"
    )
    args = parser.parse_args()
    path = args.path

    return path


def main(path):
    output_path = os.path.join(path, "output")
    text_info = utils.load_json(os.path.join(output_path, "result/texts.json"))

    layout_annotation = annotation.LayoutAnnotation(output_path, text_info)
    layout_info = layout_annotation.generate()

    image_annotation = annotation.generate_image_annotation(output_path, layout_info)
    reading_annotation = annotation.generate_reading_annotation(
        output_path, layout_info
    )
    order_annotation = annotation.generate_order_annotation(layout_info)

    layout_annotation_file = os.path.join(output_path, "result/layout_annotation.json")
    reading_annotation_file = os.path.join(
        output_path, "result/reading_annotation.json"
    )
    order_annotation_file = os.path.join(output_path, "result/order_annotation.json")

    utils.export_to_coco(layout_info, image_annotation, filename=layout_annotation_file)
    utils.export_to_json(reading_annotation, reading_annotation_file)
    utils.export_to_json(order_annotation, order_annotation_file)


if __name__ == "__main__":
    path = parse_arguments()
    main(path)
