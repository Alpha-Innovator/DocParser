import glob
import shutil
from typing import List
import re
import os
from tqdm import tqdm
import argparse
import pandas as pd

from vrdu import logger

log = logger.setup_app_level_logger(file_name="export_to_dataset.log")


json_files = [
    "layout_annotation.json",
    "order_annotation.json",
    "reading_annotation.json",
]


def extract_processed_papers(database_file: str) -> List[str]:
    df = pd.read_csv(database_file)
    processed_papers = df[df["status"] == "success"]["path"].tolist()
    return processed_papers


def export_to_dataset(processed_papers: List[str], target_path: str) -> None:
    for main_path in tqdm(processed_papers):
        output_path = os.path.join(main_path, "output")
        result_path = os.path.join(output_path, "result")

        paper_id = os.path.basename(main_path)
        discpline = os.path.basename(os.path.dirname(main_path))

        new_discpline_path = os.path.join(target_path, discpline)
        if not os.path.exists(new_discpline_path):
            os.makedirs(new_discpline_path)

        new_paper_path = os.path.join(new_discpline_path, paper_id)
        if os.path.exists(new_paper_path):
            continue
        else:
            os.makedirs(new_paper_path)

        # copy annotation files
        for json_file in json_files:
            shutil.copy(os.path.join(result_path, json_file), new_paper_path)

        # copy images
        original_image_path = os.path.join(output_path, "paper_colored")

        original_images = glob.glob(os.path.join(original_image_path, "*.jpg"))
        for image in original_images:
            filename = os.path.basename(image)
            match = re.search(r"page-(\d+)", filename)
            page_index = int(match.group(1)) - 1
            new_image_name = "original-page-{}.jpg".format(str(page_index).zfill(4))

            shutil.copy(image, os.path.join(new_paper_path, new_image_name))

        annotated_images = glob.glob(os.path.join(result_path, "*.jpg"))
        for image in annotated_images:
            shutil.copy(image, new_paper_path)


def extract_dataset(database_file: str, output_path: str):
    processed_papers = extract_processed_papers(database_file)
    export_to_dataset(processed_papers, output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--database_file", type=str, help="processed database file"
    )
    parser.add_argument("-o", "--output_path", type=str, help="output dir")
    args = parser.parse_args()

    extract_dataset(args.database_file, args.output_path)


if __name__ == "__main__":
    main()
