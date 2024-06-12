import argparse
import glob
import multiprocessing
import os

from vrdu import utils
from vrdu import logger

log = logger.setup_app_level_logger(file_name="generate_reading_annotation.log")


def generate_annotation(paper_path) -> None:
    log.debug(f"processing paper {paper_path}")
    order_json_file = os.path.join(paper_path, "order_annotation.json")

    if not os.path.exists(order_json_file):
        log.error(f"{order_json_file} does not exist.")
        return

    order_json_data = utils.load_json(order_json_file)
    if "annotations" not in order_json_data:
        log.error(f"{order_json_file} does not contain annotations.")
        return

    layout_info = order_json_data["annotations"]

    result = []

    for block in layout_info:
        result.append(
            {
                "block_id": block["block_id"],
                "bbox": block["bbox"],
                "category": block["category"],
                "page_index": block["page_index"],
                "source_code": block["source_code"],
            }
        )

    reading_json_file = os.path.join(paper_path, "reading_annotation.json")
    if os.path.exists(reading_json_file):
        log.error(f"{reading_json_file} already exists.")
        return
    utils.export_to_json(result, reading_json_file)


def generate_reading_annotation(input_path) -> None:
    discipline_paths = glob.glob(os.path.join(input_path, "*/"))

    for discipline_path in discipline_paths:
        log.debug(f"processing {discipline_path}")
        paper_paths = glob.glob(os.path.join(discipline_path, "*/"))

        with multiprocessing.Pool(34) as pool:
            pool.map(generate_annotation, paper_paths)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input_path", type=str, required=True, help="Path of dataset source"
    )
    args = parser.parse_args()
    input_path = args.input_path

    generate_reading_annotation(input_path)


if __name__ == "__main__":
    main()
