import re
import argparse
import os
from typing import Dict

from rendering.utils import export_to_json
from logger import logger

log = logger.setup_app_level_logger(file_name="app_debug.log", mode="a")


def extract_vrdu_data_from_log_file(file_path) -> Dict[str, float]:
    regex_pattern = r"\[vrdu_data_process: The (.*) is: ([-+]?\d+\.\d+)pt\]"

    extracted_data = {}

    with open(file_path, "r", encoding="latin-1") as file:
        log_content = file.read()

        for match in re.findall(regex_pattern, log_content):
            key = match[0]
            value = float(match[1])
            extracted_data[key] = value

    return extracted_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log_file", type=str, required=True, help="Path to the log file"
    )
    args = parser.parse_args()
    log_file = args.log_file

    path = os.path.dirname(log_file)
    out_path = os.path.join(path, "output/result/layout_metadata.json")
    extracted_data = extract_vrdu_data_from_log_file(log_file)
    export_to_json(extracted_data, out_path)
