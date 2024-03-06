import glob
import shutil
from typing import List
import re
import os
from tqdm import tqdm
import argparse


json_files = [
    "layout_annotation.json",
    "order_annotation.json",
    "reading_annotation.json",
]


def extract_processed_papers(input_path: str) -> List[str]:
    processed_papers = []
    contents = os.listdir(input_path)
    for content in contents:
        discpline_path = os.path.join(input_path, content)
        if not os.path.isdir(discpline_path):
            continue

        for sub_content in os.listdir(discpline_path):
            paper_path = os.path.join(discpline_path, sub_content)
            if not os.path.isdir(paper_path):
                continue

            # this paper is not successfully annotated
            result_path = os.path.join(paper_path, "output/result")
            if not os.path.exists(result_path):
                continue

            # this paper is not successfully annotated
            quality_report_file = os.path.join(result_path, "quality_report.json")
            if not os.path.exists(quality_report_file):
                continue

            # annotated json file not exist
            for json_file in json_files:
                if not os.path.exists(os.path.join(result_path, json_file)):
                    continue

            # annotated page image not exist
            if not glob.glob(os.path.join(result_path, "page*.jpg")):
                continue

            # original page image not exist
            if not glob.glob(os.path.join(paper_path, "/output/paper_colored/*.jpg")):
                continue

            processed_papers.append(result_path)

    return processed_papers


def export_to_dataset(processed_papers: List[str], output_path: str) -> None:
    for result_path in tqdm(processed_papers):
        main_path = os.path.dirname(os.path.dirname(result_path))
        paper_id = ".".join(os.path.basename(main_path).split(".", 2)[:2])

        new_paper_path = os.path.join(output_path, paper_id)
        if os.path.exists(new_paper_path):
            continue

        # copy annotatopm
        for json_file in json_files:
            shutil.copy(os.path.join(result_path, json_file), new_paper_path)

        # copy images
        colored_image_path = os.path.join(main_path, "output/paper_colored")

        original_images = glob.glob(os.path.join(colored_image_path, "*.jpg"))
        for image in original_images:
            filename = os.path.basename(image)
            match = re.search(r"page-(\d+)", filename)
            page_index = int(match.group(1)) - 1
            new_image_name = "original-page-{}.jpg".format(str(page_index).zfill(4))

            shutil.copy(image, os.path.join(new_paper_path, new_image_name))

        annotated_images = glob.glob(os.path.join(result_path, "*.jpg"))
        for image in annotated_images:
            shutil.copy(image, new_paper_path)


def extract_dataset(input_path, output_path):
    processed_papers = extract_processed_papers(input_path)
    export_to_dataset(processed_papers, output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_path", type=str, help="input dir")
    parser.add_argument("-o", "--output_path", type=str, help="output dir")
    args = parser.parse_args()

    extract_dataset(args.input_path, args.output_path)


if __name__ == "__main__":
    main()
