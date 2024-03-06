import glob
import os
import re
import pandas as pd
from datetime import datetime

from vrdu import utils
from vrdu.config import config

from vrdu import logger

log = logger.setup_app_level_logger(file_name="statistics.log")


data_file = "processed_paper_database.csv"


def extract_time(line: str) -> datetime:
    time_format = "%Y-%m-%d %H:%M:%S,%f"
    log_time = line.split(" - ")[0][1:]
    return datetime.strptime(log_time, time_format)


def init_dataframe() -> pd.DataFrame:
    if os.path.exists(data_file):
        return pd.read_csv(data_file)
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
    return df


def run_statistics():
    """store the information of processed papers into a csv file
    """
    df = init_dataframe()

    log_files = glob.glob("batch_process_*.log")
    for log_file in log_files:
        if log_file == "statistics.log":
            continue
        log.info(f"processing log file: {log_file}")

        if not os.path.exists(log_file):
            continue
        with open(log_file, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        for line in lines:
            if not line.startswith("["):
                continue

            if line.find("Line 75") != -1:
                discpline = line.split(": ")[1]
                continue

            if line.find("[VRDU] file") == -1:
                continue
            tex_file = line.split("[VRDU] file: ")[1].split(" ")[0]
            path = os.path.dirname(tex_file)
            if os.path.basename(os.path.dirname(path)) != discpline:
                log.debug(f"unknown discpline: {tex_file}")
                continue

            # extract uuid and title
            match = re.search(r"(\d+\.\d+v\d+)\.(.*)", path)
            if not match:
                continue

            uuid = match.group(1)
            title = match.group(2)

            index = df[df["uuid"] == uuid].index
            current_time = extract_time(line)

            if line.find("Line 76") != -1:  # start processing, record it
                if not index.empty:
                    continue

                # new file
                data_item = {
                    "uuid": uuid,
                    "title": title,
                    "discpline": discpline,
                    "path": path,
                    "status": "processing",
                    "start_time": str(current_time),
                    "end_time": "",
                    "error_type": "",
                    "error_info": "",
                    "date": "",
                    "pages": 0,
                    "columns": 0,
                    "blocks": 0,
                    "overlap": 0.0,
                }
                df.loc[len(df)] = data_item
                continue

            # file has been processed, update information
            if line.find("Line 83") != -1:
                if df.loc[index, "status"].item() == "success":
                    continue

                df.loc[index, "status"] = "processed"
                df.loc[index, "end_time"] = df.loc[index, "start_time"]
                continue
            # success processing file, update information
            if line.find("Line 118") != -1:
                df.loc[index, "status"] = "success"
                df.loc[index, "end_time"] = current_time
                continue
            # failed to process file, update status and eror information
            if line.find("Line 123") != -1:
                df.loc[index, "status"] = "failure"
                error_type = line.split("type: ")[1].split(",")[0]
                error_info = line.split("message: ")[1][:-1]
                df.loc[index, "error_type"] = error_type
                df.loc[index, "error_info"] = error_info
                df.loc[index, "end_time"] = current_time
                continue

    category_names = list(config.category2name.values())
    for category_name in category_names:
        df[category_name] = 0

    for index in range(len(df)):
        if df.loc[index, "status"] != "success":
            continue

        if df.loc[index, "pages"] != 0:
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

    df.to_csv(data_file)


if __name__ == "__main__":
    run_statistics()
