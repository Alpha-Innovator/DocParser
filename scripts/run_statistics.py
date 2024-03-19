import glob
import os
import pandas as pd
from datetime import datetime
import argparse
from datetime import datetime

from vrdu import utils
from vrdu.config import config

from vrdu import logger

log = logger.setup_app_level_logger(file_name="statistics.log")


database_file = "data/processed_paper_database.csv"
daily_overview_file = "data/daily_overview.csv"
discpline_info_file = "data/discpline_info.csv"


def extract_time(line: str) -> datetime:
    time_format = "%Y-%m-%d %H:%M:%S,%f"
    log_time = line.split(" - ")[0][1:]
    return datetime.strptime(log_time, time_format)


def init_dataframe() -> pd.DataFrame:
    if os.path.exists(database_file):
        return pd.read_csv(database_file, dtype={"uuid": str})
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


def update_processed_database(input_path: str):
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
            log.debug(f"uuid: {uuid}")
            current_time = extract_time(line)

            # new file
            if line.find("start processing") != -1:
                if uuid in df["uuid"].values:
                    continue

                log.debug(f"new file: {tex_file} with uuid: {uuid}")
                data_item = {
                    "index": len(df),
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
            if (
                line.find("successfully processed") != -1
                or line.find("paper has been processed") != -1
            ):
                if uuid in df["uuid"].values:
                    if df[df["uuid"] == uuid]["status"] == "success":
                        continue
                df.loc[df["uuid"] == uuid, "status"] = "success"
                df.loc[df["uuid"] == uuid, "end_time"] = current_time
                continue

            # failed to process file, update status and eror information
            if line.find("message: ") != -1:
                if uuid in df["uuid"].values:
                    if df[df["uuid"] == uuid]["status"] == "failure":
                        continue
                error_type = line.split("type: ")[1].split(", ")[0]
                error_info = line.split("message: ")[1].strip()

                df.loc[df["uuid"] == uuid, "status"] = "failure"
                df.loc[df["uuid"] == uuid, "error_type"] = error_type
                df.loc[df["uuid"] == uuid, "error_info"] = error_info
                df.loc[df["uuid"] == uuid, "end_time"] = current_time
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
        quality_report = utils.load_json(
            os.path.join(path, "output/result/quality_report.json")
        )
        df.loc[index, "pages"] = quality_report["num_pages"]
        df.loc[index, "columns"] = quality_report["num_columns"]
        df.loc[index, "blocks"] = quality_report["category_quality"][-1][
            "geometry_count"
        ]
        df.loc[index, "overlap"] = quality_report["page_quality"][-1]["ratio"]

    # remove processing files
    df = df[~(df["status"] == "processing")]
    df.to_csv(database_file, index=False)


def update_discpline_info():
    df = pd.read_csv(discpline_info_file)

    for log_file in glob.glob("data/batch_process_*.log"):
        discpline = (
            os.path.basename(log_file).split("batch_process_")[1].split(".log")[0]
        )
        with open(log_file) as f:
            lines = f.readlines()
        for line in lines:
            if line.find("[VRDU] Before filtering") != -1:
                processable_files = int(line.split("found ")[1].split(" ")[0])
                log.debug(
                    f"discpline: {discpline}, processable files: {processable_files}"
                )
                df.loc[df["discpline"] == discpline, "num_papers"] = processable_files

            if line.find("finished processing.") != -1:
                df.loc[df["discpline"] == discpline, "status"] = "complete"
            else:
                df.loc[df["discpline"] == discpline, "status"] = "processing"

    database_df = pd.read_csv(database_file)
    for index, row in df.iterrows():
        df.loc[index, "success"] = len(
            database_df[
                (database_df["discpline"] == row["discpline"])
                & (database_df["status"] == "success")
            ]
        )
        df.loc[index, "failure"] = len(
            database_df[
                (database_df["discpline"] == row["discpline"])
                & (database_df["status"] == "failure")
            ]
        )
        processed_papers = len(
            database_df[(database_df["discpline"] == row["discpline"])]
        )

        df.loc[index, "processed"] = processed_papers

    df.to_csv(discpline_info_file, index=False)


def update_daily_overview() -> None:
    daily_df = pd.read_csv(daily_overview_file)
    database_df = pd.read_csv(database_file)

    num_total_papers = database_df.shape[0]
    num_total_processed = database_df[database_df["status"] == "success"].shape[0]

    last_index = daily_df.index[-1]
    num_daily_papers = num_total_papers - daily_df.loc[last_index, "#total papers"]
    num_daily_processed = (
        num_total_processed - daily_df.loc[last_index, "#total processed"]
    )

    if num_total_papers == daily_df.loc[last_index, "#total papers"]:
        log.info("Please update database file before running this script.")

    daily_df.loc[last_index + 1, "date"] = datetime.today().strftime("%Y-%m-%d")
    daily_df.loc[last_index + 1, "#daily papers"] = num_daily_papers
    daily_df.loc[last_index + 1, "#daily processed"] = num_daily_processed
    daily_df.loc[last_index + 1, "#total papers"] = num_total_papers
    daily_df.loc[last_index + 1, "#total processed"] = num_total_processed
    daily_df.loc[last_index + 1, "#discplines"] = database_df["discpline"].nunique()
    daily_df["daily pass ratio"] = (
        daily_df["#daily processed"] / daily_df["#daily papers"]
    )
    daily_df["total pass ratio"] = (
        daily_df["#total processed"] / daily_df["#total papers"]
    )

    daily_df.to_csv("data/daily_overview.csv", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, default="data/")
    args = parser.parse_args()

    update_processed_database(args.input_path)

    update_daily_overview()

    update_discpline_info()


if __name__ == "__main__":
    main()
