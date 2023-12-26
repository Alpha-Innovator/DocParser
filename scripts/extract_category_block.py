import os
import shutil
from typing import List
import uuid
import datetime
import argparse

from vrdu import utils
from vrdu.config import config


def extract_category(path: str, category: int, output_directory: str) -> List:
    """
    Extracts blocks from the given 'path' that match the specified 'category'
    and saves the corresponding images to 'output_directory'.

    Args:
        path (str): The path to the directory containing the source JSON file.
        category (int): The category index to filter blocks by.
        output_directory (str): The path to the directory where the extracted images will be saved.

    Returns:
        list: A list of blocks that match the specified category.
    """
    # load block-source_code informations
    source_json_file = os.path.join(path, "reading_annotation.json")
    data = utils.load_json(source_json_file)

    result = []
    for key, blocks in data.items():
        # key must be page index
        if not key.isnumeric():
            continue
        for block in blocks:
            if "category" not in block:
                continue
            if block["category"] == category:
                result.append(block)

    # save images
    for key in result:
        output_image_name = f"{uuid.uuid4()}.png"
        shutil.copyfile(
            os.path.join(path, key["image_path"]),
            os.path.join(output_directory, output_image_name),
        )
        key["image_path"] = output_image_name
        key["paper_source"] = path
        key["added_date"] = str(datetime.date.today())
        key["macros"] = data.get("macros", [])

    return result


def extract_category_dataset(
    category_name: str,
    input_directory: str,
    output_directory: str,
    existed_source_json: str = None,
):
    """
    Extracts blocks from the given 'input_directory' that match the specified 'category_name'
    and saves the corresponding images to 'output_directory'.

    Args:
        category_name (str): The name of the category to extract.
        input_directory (str): The path to the directory containing the source JSON file (recursively).
        output_directory (str): The path to the directory where the extracted images will be saved.
        existed_source_json (str, optional): The path to the JSON file that contains the extracted data,
            used to filter out the data that has already been extracted.

    Returns:
        None
    """
    if category_name not in config.name2category.keys():
        raise KeyError(
            f"Unknown category name, avalaible category names: {list(config.name2category.keys())}"
        )

    category = config.name2category[category_name]
    result_json = os.path.join(output_directory, "reading_annotation.json")

    existed_source = set()
    results = []
    # use the existed json as a filter (used when to add data to a new dataset
    # but expect to separate from an existing dataset)
    if os.path.exists(existed_source_json):
        existed_source = set(
            item["paper_source"] for item in utils.load_json(result_json)
        )
        results = utils.load_json(result_json)
    # use the result json as a filter (used when to add data to an existing dataset)
    elif os.path.exists(result_json):
        results = utils.load_json(result_json)

    count = 0
    for root, dirs, files in os.walk(input_directory):
        if "reading_annotation.json" not in files:
            continue

        # if data of this folder has been extracted
        if root in existed_source:
            continue

        count += 1
        results.extend(extract_category(root, category, output_directory))

    # exclude the reading_annotation.json file
    num_of_samples = len(os.listdir(output_directory)) - 1
    utils.export_to_json(results, result_json)
    print(
        f"{num_of_samples} of {category_name} samples obtained by extracting {count} files."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--category_name",
        type=str,
        help="the name of the category to extract, such as 'Figure' or 'Table'",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--input_directory",
        type=str,
        help="the directory to extract from, recursively",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_directory",
        type=str,
        help="the directory to save the result",
        required=True,
    )
    parser.add_argument(
        "-e", "--existed_source", type=str, help="the json dictionary to exclude from"
    )
    args = parser.parse_args()
    category_name = args.category_name
    input_directory = args.input_directory
    output_directory = args.output_directory
    existed_source_json = args.existed_source

    extract_category_dataset(
        category_name, input_directory, output_directory, existed_source_json
    )


if __name__ == "__main__":
    main()
