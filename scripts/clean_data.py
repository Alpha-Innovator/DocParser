import argparse
import re
from typing import Dict, List
import os

from vrdu import utils
from vrdu import logger

log = logger.setup_app_level_logger(file_name="clean_data.log")


def expand_column_patterns(column_patterns) -> str:
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


def clean_tabular(data: Dict) -> Dict:
    data["quality"] = "high"
    # filter all non-compilable data
    if not utils.compile_check(data["source_code"]):
        data["quality"] = "uncompiable"

    # count the number of rows and columns
    cols_match = re.search(
        r"\\begin{tabular}\n?(?:\[.*?\])?{(.*)}", data["source_code"]
    )

    if not cols_match:
        log.debug(f"cols not found for {data}")
        return
    cols = cols_match.group(1)

    align_patterns = ["c", "r", "l", "p"]
    expanded_cols = expand_column_patterns(cols)
    num_columns = sum(expanded_cols.count(ch) for ch in align_patterns)
    data["cols"] = num_columns
    num_rows = data["source_code"].count("\\\\")
    data["rows"] = num_rows

    # mark table with < 3 columns as low quality
    if num_columns < 3:
        data["quality"] = "low"

    return data


def clean_table_dataset(reading_annotations: List[Dict]) -> List[Dict]:
    result = []
    for data in reading_annotations:
        cleaned_data = clean_tabular(data)
        result.append(cleaned_data)

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dataset_path", required=True, help="path to category png-latex dataset"
    )
    parser.add_argument("-t", "--type", required=True, help="equation or table")
    args = parser.parse_args()
    dataset_path, dataset_type = args.dataset_path, args.type

    reading_annotation_file = os.path.join(dataset_path, "reading_annotation.json")
    if not os.path.exists(reading_annotation_file):
        raise FileNotFoundError(f"{reading_annotation_file} NOT Exists!")

    reading_annotations = utils.load_json(reading_annotation_file)

    if dataset_type.lower() == "table":
        cleaned_reading_annotations = clean_table_dataset(reading_annotations)
        utils.export_to_json(
            cleaned_reading_annotations,
            os.path.join(dataset_path, "clean_reading_annotation_v2.json"),
        )
    elif dataset_type.lower() == "equation":
        pass


if __name__ == "__main__":
    main()
