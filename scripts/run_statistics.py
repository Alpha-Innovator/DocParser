import glob
import os
import re
import pandas as pd
from datetime import datetime

from vrdu import utils
from vrdu.config import config

from vrdu import logger

log = logger.setup_app_level_logger(file_name="statistics.log")


def extract_time(line: str):
    time_format = "%Y-%m-%d %H:%M:%S,%f"
    log_time = line.split(" - ")[0][1:]
    return datetime.strptime(log_time, time_format)


def init_dataframe() -> pd.DataFrame:
    columns = [
        "uuid",
        "title",
        "discpline",
        "path",
        "status",
        "start_time",
        "end_time",
        "error_type",
        "error_info",
        "date",
        "pages",
        "columns",
        "blocks",
        "overlap",
    ]
    df = pd.DataFrame(columns=columns)

    # df["duration"] = pd.to_timedelta(df["duration"], unit="sec")
    return df


def run_statistics_v2():
    df = init_dataframe()

    pattern = r"(\d+\.\d+v\d+)\.(.*)"  # used for filter uuid and title

    log_files = glob.glob("batch_process_*.log")
    for log_file in log_files:
        log.debug(f"processing log file: {log_file}")
        discpline = "unknown"
        with open(log_file, "r") as f:
            for line in f.readlines():
                log.debug(f"line={line}")
                if not line.startswith("["):
                    continue
                if line.find("Line 139") != -1:  # determine discpline
                    index = line.find("category: ")
                    discpline = line[index + len("category: ") : -1]
                    log.debug(f"displine: {discpline}")
                    continue
                if line.find("Line 74") != -1:  # start processing, record it
                    index = line.find("processing file ")
                    file = line[index + len("processing file ") :]
                    log.debug(f"processing file {file}")
                    path = os.path.dirname(file)
                    if os.path.basename(os.path.dirname(path)) != discpline:
                        log.debug(f"unknown discpline: {file}")
                        continue

                    match = re.search(pattern, path)
                    if not match:
                        log.debug(f"unknown path: {path}")
                        continue

                    uuid = match.group(1)
                    title = match.group(2)

                    if uuid in df["uuid"].values:
                        # paper has been processed
                        continue

                    start_time = extract_time(line)
                    data = [
                        uuid,
                        title,
                        discpline,
                        path,
                        "unknown",
                        str(start_time),
                        "",
                        "",
                        "",
                        "",
                        0,
                        0,
                        0,
                        0.0,
                    ]
                    df.loc[len(df)] = data
                    continue
                # file has been processed, update information
                if line.find("Line 79") != -1:
                    file = line.split("File ")[1].split(" ")[0]
                    path = os.path.dirname(file)
                    if os.path.basename(os.path.dirname(path)) != discpline:
                        log.debug(f"unknown discpline: {file}")
                        continue

                    pattern = r"(\d+\.\d+v\d+)\.(.*)"
                    match = re.search(pattern, path)
                    if not match:
                        log.debug(f"unknown path: {path}")
                        continue

                    uuid = match.group(1)
                    title = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index

                    df.loc[existed_index, "status"] = "processed"
                    df.loc[existed_index, "end_time"] = df.loc[
                        existed_index, "start_time"
                    ]
                    continue
                # success processing file, update information
                if line.find("Line 103") != -1:
                    index = line.find("processing file ")
                    file = line[index + len("processing file ") :]
                    path = os.path.dirname(file)
                    if os.path.basename(os.path.dirname(path)) != discpline:
                        log.debug(f"unknown discpline: {file}")
                        continue

                    match = re.search(pattern, path)
                    if not match:
                        log.debug(f"unknown path: {path}")
                        continue

                    uuid = match.group(1)
                    title = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index

                    df.loc[existed_index, "status"] = "success"
                    end_time = extract_time(line)

                    df.loc[existed_index, "end_time"] = end_time
                    continue
                # failed to process file, update status and eror information
                if line.find("Line 108") != -1:
                    # Extract variables using split()
                    file = line.split("processing file ")[1].split(",")[0]
                    error_type = line.split("type: ")[1].split(",")[0]
                    error_info = line.split("message: ")[1][:-1]
                    path = os.path.dirname(file)
                    if os.path.basename(os.path.dirname(path)) != discpline:
                        log.debug(f"unknown discpline: {file}")
                        continue

                    match = re.search(pattern, path)
                    if not match:
                        log.debug(f"unknown discpline: {discpline}")
                        continue

                    uuid = match.group(1)
                    title = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index

                    df.loc[existed_index, "status"] = "failure"
                    df.loc[existed_index, "error_type"] = error_type
                    df.loc[existed_index, "error_info"] = error_info
                    end_time = extract_time(line)

                    df.loc[existed_index, "end_time"] = end_time
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
        df.loc[index, "pages"] = quality_report["num_pages"]
        df.loc[index, "columns"] = quality_report["num_columns"]
        df.loc[index, "blocks"] = quality_report["category_quality"][-1][
            "geometry_count"
        ]
        df.loc[index, "overlap"] = quality_report["page_quality"][-1]["ratio"]

        for item in quality_report["category_quality"]:
            log.debug(f"category: {item['category']}")
            if item["category"] in category_names:
                df.loc[index, item["category"]] = item["geometry_count"]

        layout_annotation_file = os.path.join(result_path, "layout_annotation.json")
        layout_annotation = utils.load_json(layout_annotation_file)
        df.loc[index, "date"] = layout_annotation["info"]["date_created"]

    df.to_csv("data.csv", index=False)


if __name__ == "__main__":
    # path = "/cpfs01/shared/ADLab/datasets/arxiv_source/arxiv_source_uncompressed/"
    # run_statistics_v1(path)
    run_statistics_v2()
