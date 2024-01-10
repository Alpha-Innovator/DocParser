from collections import defaultdict
import glob
import os
import re
from typing import Dict
import csv
import pandas as pd
from datetime import datetime

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


def extract_time(line: str):
    time_format = "%Y-%m-%d %H:%M:%S,%f"
    log_time = line.split(" - ")[0][1:]
    return datetime.strptime(log_time, time_format)


def run_statistics_v2():
    all_categories = utils.get_all_categories()
    columns = [
        "uuid",
        "title",
        "category",
        "path",
        "status",
        "duration",
        "error_type",
        "error_info",
        "date",
        "pages",
        "columns",
        "blocks",
        "overlap",
    ]
    df = pd.DataFrame(columns=columns)
    df['duration'] = pd.to_timedelta(df["duration"])

    start_times = {}

    log_files = glob.glob("batch_process_*.log")
    for log_file in log_files:
        category = "unknown"
        with open(log_file, "r") as f:
            for line in f.readlines():
                if not line.startswith("["):
                    continue
                if line.find("Line 139") != -1:  # determine category
                    index = line.find("category: ")
                    category = line[index + len("category: ") : -1]
                    continue
                if line.find("Line 74") != -1:  # start processing, record it
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
                    start_time = extract_time(line)
                    start_times[uuid] = start_time

                    data = [
                        uuid,
                        name,
                        category,
                        path,
                        "unknown",
                        0,
                        "",
                        "",
                        line[1:11],
                        0,
                        0,
                        0,
                        0.0,
                    ]
                    df.loc[len(df)] = data
                    continue
                if (
                    line.find("Line 79") != -1
                ):  # file has been processed, update information
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
                    df.loc[existed_index, "duration"] = 0.0
                    continue
                if (
                    line.find("Line 103") != -1
                ):  # success processing file, update information
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
                    end_time = extract_time(line)

                    df.loc[existed_index, "duration"] = end_time - start_times[uuid]
                    continue
                if (
                    line.find("Line 108") != -1
                ):  # failed to process file, update status and eror information
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

                    if df.loc[existed_index, "status"].str == "success":
                        continue

                    df.loc[existed_index, "status"] = "failure"
                    df.loc[existed_index, "error_type"] = error_type
                    df.loc[existed_index, "error_info"] = error_info
                    end_time = extract_time(line)

                    df.loc[existed_index, "duration"] = end_time - start_times[uuid]
                    continue

    category_names = list(config.category2name.values())
    for category_name in category_names:
        df[category_name] = 0

    for index in range(len(df)):
        if df.loc[index, "status"] != "success":
            continue
        # use output result to update information
        path = df.loc[index, "path"]
        result_path = os.path.join(path, "output/result")
        quality_report_file = os.path.join(result_path, "quality_report.json")
        quality_report = utils.load_json(quality_report_file)
        log.debug(f"keys: {list(quality_report.keys())}")
        df.loc[index, "pages"] = quality_report["num_pages"]
        df.loc[index, "columns"] = quality_report["num_columns"]
        df.loc[index, "blocks"] = quality_report["category_quality"][-1][
            "geometry_count"
        ]
        df.loc[index, "overlap"] = quality_report["page_quality"][-1]["ratio"]
        log.debug(
            f'pages: {df.loc[index, "pages"]}, columns: {df.loc[index, "columns"]}'
        )

        for item in quality_report["category_quality"]:
            log.debug(f"category: {item['category']}")
            if item["category"] in category_names:
                df.loc[index, item["category"]] = item["geometry_count"]

    df.to_csv("data.csv", index=False)


if __name__ == "__main__":
    # path = "/cpfs01/shared/ADLab/datasets/arxiv_source/arxiv_source_uncompressed/"
    # run_statistics_v1(path)
    run_statistics_v2()
