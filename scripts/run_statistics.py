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
    if os.path.exists("data.csv"):
        df = pd.read_csv("data.csv")
    else:
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

    # df["duration"] = pd.to_timedelta(df["duration"], unit="sec")
    return df


def run_statistics_v2():
    df = init_dataframe()

    all_discplines = list(
        pd.read_csv("scripts/category_count.csv")["categories"].values
    )

    start_times = {}

    pattern = r"(\d+\.\d+v\d+)\.(.*)"  # used for filter uuid and title

    log_files = glob.glob("batch_process_*.log")
    for log_file in log_files:
        log.debug(f"processing log file: {log_file}")
        discpline = "unknown"
        with open(log_file, "r") as f:
            for line in f.readlines():
                if not line.startswith("["):
                    continue
                if line.find("Line 139") != -1:  # determine category
                    index = line.find("category: ")
                    discpline = line[index + len("category: ") : -1]
                    continue
                if line.find("Line 74") != -1:  # start processing, record it
                    index = line.find("processing file ")
                    file = line[index + len("processing file ") :]
                    log.debug(f"processing file {file}")
                    path = os.path.dirname(file)
                    discpline = os.path.basename(os.path.dirname(path))
                    if discpline not in all_discplines:
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
                    start_times[uuid] = start_time
                    log.debug(f"start time: {start_times[uuid]}")
                    data = [
                        uuid,
                        title,
                        discpline,
                        path,
                        "unknown",
                        0,
                        "",
                        "",
                        "",
                        0,
                        0,
                        0,
                        0.0,
                    ]
                    extended_data = data + [0] * (len(df.columns.to_list()) - len(data))
                    df.loc[len(df)] = extended_data
                    continue
                # file has been processed, update information
                if line.find("Line 79") != -1:
                    file = line.split("File ")[1].split(" ")[0]
                    path = os.path.dirname(file)
                    discpline = os.path.basename(os.path.dirname(path))
                    if discpline not in all_discplines:
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

                    if df.loc[existed_index, "status"].str == "unknown":
                        df.loc[existed_index, "status"] = "processed"
                        df.loc[existed_index, "duration"] = 0.0
                    continue
                # success processing file, update information
                if line.find("Line 103") != -1:
                    index = line.find("processing file ")
                    file = line[index + len("processing file ") :]
                    path = os.path.dirname(file)
                    discpline = os.path.basename(os.path.dirname(path))
                    if discpline not in all_discplines:
                        log.debug(f"unknown discpline: {file}")
                        continue

                    match = re.search(pattern, path)
                    if not match:
                        log.debug(f"unknown path: {path}")
                        continue

                    uuid = match.group(1)
                    title = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index
                    if df.loc[existed_index, "status"].str == "unknown":
                        df.loc[existed_index, "status"] = "success"
                        end_time = extract_time(line)

                        log.debug(
                            f"end time={end_time}, start time: {start_times[uuid]}"
                        )
                        df.loc[existed_index, "duration"] = end_time - start_times[uuid]
                    continue
                # failed to process file, update status and eror information
                if line.find("Line 108") != -1:
                    # Extract variables using split()
                    file = line.split("processing file ")[1].split(",")[0]
                    error_type = line.split("type: ")[1].split(",")[0]
                    error_info = line.split("message: ")[1][:-1]
                    path = os.path.dirname(file)
                    discpline = os.path.basename(os.path.dirname(path))
                    if discpline not in all_discplines:
                        continue

                    match = re.search(pattern, path)
                    if not match:
                        log.debug(f"unknown discpline: {discpline}")
                        continue

                    uuid = match.group(1)
                    title = match.group(2)
                    existed_index = df[df["uuid"] == uuid].index

                    if df.loc[existed_index, "status"].str != "unknown":
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

        layout_annotation_file = os.path.join(result_path, "layout_annotation.json")
        layout_annotation = utils.load_json(layout_annotation_file)
        df.loc[index, "date"] = layout_annotation["info"]["date_created"]

    df.to_csv("data.csv", index=False)


if __name__ == "__main__":
    # path = "/cpfs01/shared/ADLab/datasets/arxiv_source/arxiv_source_uncompressed/"
    # run_statistics_v1(path)
    run_statistics_v2()
