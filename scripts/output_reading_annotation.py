import os
import argparse


from annotation.reading.reading_annotation_generator import generate_reading_annotation
from rendering.utils import export_to_json, load_json
from logger import logger
from config import config

log = logger.setup_app_level_logger(file_name="app_debug.log", mode="a")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path", type=str, required=True, help="The path to the main directory"
    )
    args = parser.parse_args()
    result_path = args.path
    return result_path


def main():
    # generate text annotation info
    result_path = parse_arguments()
    log.debug(f"result_path: {result_path}")
    reading_info = load_json(os.path.join(result_path, "texts.json"))
    geometry_info = load_json(os.path.join(result_path, "layout_annotation.json"))
    category_info = load_json(os.path.join(result_path, "category_annotation.json"))

    result = generate_reading_annotation(geometry_info, category_info, reading_info)
    text_json_file = os.path.join(result_path, "reading_annotation.json")
    export_to_json(result, text_json_file)


if __name__ == "__main__":
    main()
