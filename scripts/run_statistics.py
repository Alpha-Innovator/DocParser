import glob
import os
import re
import pandas as pd
from datetime import datetime
import argparse

from vrdu import utils
from vrdu.config import config

from vrdu import logger

log = logger.setup_app_level_logger(file_name="statistics.log")


data_file = "data/processed_paper_database.csv"


def extract_time(line: str) -> datetime:
    time_format = "%Y-%m-%d %H:%M:%S,%f"
    log_time = line.split(" - ")[0][1:]
    return datetime.strptime(log_time, time_format)


def init_dataframe() -> pd.DataFrame:
    if os.path.exists(data_file):
        return pd.read_csv(data_file)
    columns = [
        "uuid",
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


def run_statistics(input_path: str):
    """store the information of processed papers into a csv file"""
    df = init_dataframe()

    log_files = glob.glob(os.path.join(input_path, "batch_process_*.log"))
    for log_file in log_files:
        log.info(f"processing log file: {log_file}")

        if not os.path.exists(log_file):
            continue
        with open(log_file, "r") as f:
            lines = [line.strip() for line in f.readlines()]

        for line in lines:
            if not line.startswith("["):
                continue

            if line.find("start to process") != -1:
                discpline = line.split("discpline: ")[1].split(", ")[0]
                continue

            if line.find("[VRDU] file") == -1:
                continue
            tex_file = line.split("[VRDU] file: ")[1].split(", ")[0]
            path = os.path.dirname(tex_file)
            if os.path.basename(os.path.dirname(path)) != discpline:
                log.debug(f"unknown discpline: {tex_file}")
                continue

            # extract uuid and title
            uuid = os.path.basename(path)

            index = df[df["uuid"] == uuid].index
            current_time = extract_time(line)

            # new file
            if line.find("start processing") != -1:
                if not index.empty:
                    continue
                data_item = {
                    "uuid": uuid,
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

            # success processing file, update information
            if line.find("successfully processed") != -1:
                df.loc[index, "status"] = "success"
                df.loc[index, "end_time"] = current_time
                continue
            # failed to process file, update status and eror information
            if line.find("message: ") != -1:
                df.loc[index, "status"] = "failure"
                error_type = line.split("type: ")[1].split(", ")[0]
                error_info = line.split("message: ")[1].strip()
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
            if item["category"] in category_names:
                df.loc[index, item["category"]] = item["geometry_count"]

        layout_annotation_file = os.path.join(result_path, "layout_annotation.json")
        layout_annotation = utils.load_json(layout_annotation_file)
        df.loc[index, "date"] = layout_annotation["info"]["date_created"]

    df.to_csv(data_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, default="data/")
    args = parser.parse_args()
    run_statistics(args.input_path)


if __name__ == "__main__":
    main()
