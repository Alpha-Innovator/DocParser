from collections import defaultdict
import glob
import os
import re
from typing import Dict
import csv
import pandas as pd

from vrdu import utils
from vrdu.config import config

from vrdu import logger

log = logger.setup_app_level_logger(file_name="statistics.log")


def is_standalone(path: str) -> bool:
    with open(path, "r") as f:
        content = f.read()
    return "standalone" in content


def analyze_result(path) -> Dict:
    """
    Analyzes the processed result of the given path. This is done by checking if the
    result files exist.

    Args:
        path (str): The path to the directory containing the result files.

    Returns:
        Dict: A dictionary containing the statistics for each category.

    Raises:
        None.
    """

    # all_categories = utils.get_all_categories()
    all_categories = ["cs.DS"]

    success_files = defaultdict(list)
    total_files = defaultdict(list)
    standalone_files = []
    others = []

    for category in all_categories:
        category_path = os.path.join(path, category)
        all_tex_files = utils.extract_tex_files(category_path)

        for tex_file in all_tex_files:
            root = os.path.dirname(tex_file)
            category = os.path.dirname(root).split("/")[-1]
            if category not in all_categories:
                if is_standalone(tex_file):
                    standalone_files.append(tex_file)
                else:
                    others.append(tex_file)
            elif os.path.exists(
                os.path.join(root, "output/result/quality_report.json")
            ):
                success_files[category].append(tex_file)

            total_files[category].append(tex_file)

    data = {
        "main": {
            category: {
                "total": total_files[category],
                "successed": success_files[category],
                "rate": (len(success_files[category]) / len(total_files[category]))
                * 100,
            }
            for category in total_files
        },
        "standalone": standalone_files,
        "others": others,
    }

    return data


def run_statistics_v1(path):
    data = analyze_result(path)
    categories = utils.get_all_categories()
    with open("statistics.csv", "w") as f:
        fieldnames = ["category", "total", "successed"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in categories:
            if key not in data["main"]:
                continue
            writer.writerow(
                {
                    "category": key,
                    "total": len(data["main"][key]["total"]),
                    "successed": len(data["main"][key]["successed"]),
                }
            )
    utils.export_to_json(data, "result_statistics.json")


def run_statistics_v2():
    all_categories = utils.get_all_categories()
    columns = [
        "uuid",
        "title",
        "category",
        "path",
        "status",
        "error_type",
        "error_info",
        "date",
        "pages",
        "columns",
        "blocks",
        # *list(config.category2name.values()),
        "overlap",
    ]
    df = pd.DataFrame(columns=columns)
    log_files = glob.glob("batch_process_*.log")
    for log_file in log_files:
        category = "unknown"
        with open(log_file, "r") as f:
            for line in f.readlines():
                if not line.startswith("["):
                    continue
                if line.find("Line 139") != -1:
                    index = line.find("category: ")
                    category = line[index + len("category: ") : -1]
                    continue
                if line.find("Line 74") != -1:
                    index = line.find("processing file ")
                    file = line[index + len("processing file ") :]
                    path = os.path.dirname(file)
                    category_path = os.path.basename(os.path.dirname(path))
                    if category_path not in all_categories:
                        continue

                    pattern = r"(\d+\.\d+v\d+)\.(.*)"
                    match = re.search(pattern, path)
                    if not match:
                        continue

                    uuid = match.group(1)
                    name = match.group(2)
                    data = [
                        uuid,
                        name,
                        category,
                        path,
                        "unknown",
                        "",
                        "",
                        line[1:11],
                        0,
                        0,
                        0,
                        0.0,
                    ]
                    df.loc[len(df)] = data
                    log.debug(f"data numbers: {len(df)}")
                    continue
                if line.find("Line 79") != -1:
                    file = line.split("File ")[1].split(" ")[0]
                    path = os.path.dirname(file)
                    category_path = os.path.basename(os.path.dirname(path))
                    if category_path not in all_categories:
                        continue

                    pattern = r"(\d+\.\d+v\d+)\.(.*)"
                    match = re.search(pattern, path)
                    if not match:
                        continue

                    uuid = match.group(1)
                    name = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index

                    df.loc[existed_index, "status"] = "success"
                    continue
                if line.find("Line 103") != -1:
                    index = line.find("processing file ")
                    file = line[index + len("processing file ") :]
                    path = os.path.dirname(file)
                    category_path = os.path.basename(os.path.dirname(path))
                    if category_path not in all_categories:
                        continue

                    pattern = r"(\d+\.\d+v\d+)\.(.*)"
                    match = re.search(pattern, path)
                    if not match:
                        continue

                    uuid = match.group(1)
                    name = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index

                    df.loc[existed_index, "status"] = "success"
                    continue
                if line.find("Line 108") != -1:
                    # Extract variables using split()
                    file_name = line.split("processing file ")[1].split(",")[0]
                    error_type = line.split("type: ")[1].split(",")[0]
                    error_info = line.split("message: ")[1][:-1]
                    path = os.path.dirname(file_name)
                    category_path = os.path.basename(os.path.dirname(path))
                    if category_path not in all_categories:
                        continue

                    pattern = r"(\d+\.\d+v\d+)\.(.*)"
                    match = re.search(pattern, path)
                    if not match:
                        continue

                    uuid = match.group(1)
                    name = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index

                    df.loc[existed_index, "status"] = "failure"
                    df.loc[existed_index, "error_type"] = error_type
                    df.loc[existed_index, "error_info"] = error_info
                    continue

    df.to_csv("data.csv", index=False)


if __name__ == "__main__":
    # path = "/cpfs01/shared/ADLab/datasets/arxiv_source/arxiv_source_uncompressed/"
    # run_statistics_v1(path)
    run_statistics_v2()
