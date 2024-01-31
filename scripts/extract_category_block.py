import os
import re
import shutil
from typing import List, Optional, Dict
import uuid
import datetime
import argparse

from vrdu import utils
from vrdu.config import config

from vrdu import logger

log = logger.setup_app_level_logger(file_name="extract_category.log")


def expand_column_patterns(column_patterns: str) -> str:
    expanded_columns = ""
    pattern_parts = column_patterns.split("|")
    for pattern in pattern_parts:
        if pattern.startswith("*{") and pattern.endswith("}"):
            sub_pattern = pattern[2:-1]
            num, form = sub_pattern.split("}{")
            num = int(num)
            expanded_columns += form * num
        else:
            expanded_columns += pattern
        expanded_columns += "|"
    return expanded_columns.rstrip("|")


def add_layout_information(tabular: Dict) -> Dict:
    tabular["cols"] = 0
    tabular["rows"] = 0
    # count the number of rows and columns
    cols_match = re.search(
        r"\\begin{tabular}\n?(?:\[.*?\])?{(.*)}", tabular["source_code"]
    )

    if not cols_match:
        log.debug(f"cols not found for {tabular}")
        return tabular
    cols = cols_match.group(1)

    align_patterns = ["c", "r", "l", "p"]
    try:
        expanded_cols = expand_column_patterns(cols)
    except Exception:
        log.exception(f"Error processing data: {tabular}")
        return tabular

    num_columns = sum(expanded_cols.count(ch) for ch in align_patterns)
    tabular["cols"] = num_columns
    num_rows = tabular["source_code"].count("\\\\")
    tabular["rows"] = num_rows

    # mark table with < 3 columns as low quality
    if num_columns < 3:
        tabular["quality"] = "low"

    return tabular


def add_linguistic_information(sentence: Dict) -> None:
    # 1. count the number of words
    # 2. extract all inline equations
    pattern = r"(\\\(.*?\\\))|(\$.*?\$)|(\\begin\{math\}.*?\\end\{math\})"
    matches = re.findall(pattern, sentence["source_code"])

    sentence["inline_equations"] = [match[1] for match in matches]
    result = re.sub(pattern, "", sentence["source_code"])
    sentence["num_words"] = len(result.split())


def extract_category(
    input_directory: str, category_name: str, output_directory: str
) -> List:
    """
    Extracts blocks from the given 'path' that match the specified 'category'
    and saves the corresponding images to 'output_directory'.

    Args:
        input_directory (str): The path to the directory containing the source JSON file.
        category_name (str): The name of the category to extract.
        output_directory (str): The path to the directory where the extracted images will be saved.

    Returns:
        List: A tuple containing the high-quality blocks and the low-quality blocks.
    """
    category_index = config.name2category[category_name]
    # load block-source_code information
    source_json_file = os.path.join(input_directory, "reading_annotation.json")
    data = utils.load_json(source_json_file)

    result = []
    for key, blocks in data.items():
        # key must be page index
        if not key.isnumeric():
            continue
        for block in blocks:
            if "category" not in block:
                continue
            if block["category"] != category_index:
                continue

            if utils.compile_check(block["source_code"]):
                block["quality"] = "high"
            else:
                block["quality"] = "uncompiable"

            # add layout information for tabular data
            if category_name == "Table":
                block = add_layout_information(block)
            if category_name == "Text-EQ":
                add_linguistic_information(block)

            # ignores all identical blocks
            if result and block["source_code"] == result[-1]["source_code"]:
                result.pop()
                continue
            result.append(block)

    # save images
    for key in result:
        output_image_name = f"{uuid.uuid4()}.png"
        shutil.copyfile(
            os.path.join(input_directory, key["image_path"]),
            os.path.join(output_directory, output_image_name),
        )
        key["image_path"] = output_image_name
        key["paper_source"] = input_directory
        key["added_date"] = str(datetime.date.today())

    return result


def extract_category_dataset(
    category_name: str,
    input_directory: str,
    output_directory: str,
    existed_source_json: Optional[str] = None,
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

    Raises:
        KeyError: If the specified 'category_name' is not found in the 'config.name2category' dictionary.
    """
    log.info(f"extract {category_name} data from {input_directory}")
    if category_name not in config.name2category.keys():
        raise KeyError(
            f"Unknown category name, avalaible category names: {list(config.name2category.keys())}"
        )

    result_json = os.path.join(output_directory, "reading_annotation.json")

    existed_source = set()
    results = []
    # use the existed json as a filter (used when to add data to a new dataset
    # but expect to separate from an existing dataset)
    if existed_source_json is None:
        existed_source_json = result_json

    if os.path.exists(existed_source_json):
        existed_source = set(
            item["paper_source"] for item in utils.load_json(existed_source_json)
        )
        results = utils.load_json(existed_source_json)

    log.info(f"there ere {len(results)} existed data items")
    for root, dirs, files in os.walk(input_directory):
        if "reading_annotation.json" not in files:
            continue

        # if data of this folder has been extracted
        if root in existed_source:
            continue

        results.extend(extract_category(root, category_name, output_directory))

    # exclude the reading_annotation.json file
    num_of_samples = len(os.listdir(output_directory)) - 1
    utils.export_to_json(results, result_json)
    log.info(f"{num_of_samples} of {category_name} samples obtained.")


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
