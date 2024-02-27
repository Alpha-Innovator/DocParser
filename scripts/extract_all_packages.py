import argparse
from collections import defaultdict
import multiprocessing
import os
import re
from typing import DefaultDict, List
import pandas as pd


from vrdu import utils
from vrdu import logger


log = logger.setup_app_level_logger(file_name="extract_all_packages.log")


def process_one_file(tex_file) -> DefaultDict[str, int]:
    result = defaultdict(int)
    try:
        with open(tex_file) as f:
            tex_content = f.read()
        pattern = r"\\usepackage(?:\[.*?\])?{([^}]+)}"
        envs = re.findall(pattern, tex_content)

        for env in envs:
            packages = env.split(",")
            for package in packages:
                result[package.strip()] += 1

    except UnicodeError:
        log.debug(f"failed to open tex file: {tex_file}")
    finally:
        return result


def process_batch(
    tex_files: List[str],
    json_file: str,
    cpu_count: int,
    batch_size: int = 100,
) -> None:
    """Given a list of tex files, process this list batch by batch

    Args:
        tex_files (List[str]): a list of .tex files
        json_file (str): a json file to store results
        cpu_count (int): number of cpus used for multiprocess.Pool
        batch_size (int, optional): _description_. Defaults to 100.
    """
    for i in range(0, len(tex_files), batch_size):
        batch_tex_files = tex_files[i : i + batch_size]
        with multiprocessing.Pool(cpu_count) as pool:
            results = pool.map(process_one_file, batch_tex_files)

        # use append mode to update json file
        json_data = {}
        if os.path.exists(json_file):
            json_data = utils.load_json(json_file)

        for result in results:
            for k, v in result.items():
                if k not in json_data:
                    json_data[k] = 0
                json_data[k] += v
        utils.export_to_json(json_data, json_file)

        log.info(f"processed {i,i + batch_size}-th batch")


def extract_discpline_env(path, cpu_count, discpline):
    log.info(f"processing discpline: {discpline}")
    discpline_path = os.path.join(path, discpline)
    tex_files = utils.extract_all_tex_files(discpline_path)
    log.info(f"there are {len(tex_files)} tex_files")
    json_file = "all_packages.json"
    process_batch(tex_files, json_file, cpu_count, 1000)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, required=True)
    parser.add_argument("-c", "--cpu_count", type=int, required=True)
    parser.add_argument("-t", "--discpline", type=str, required=False)
    args = parser.parse_args()
    path, cpu_count, discpline = args.path, args.cpu_count, args.discpline

    batch_df = pd.read_csv(
        "/cpfs01/shared/ADLab/datasets/arxiv_source/arxiv_source_uncompressed_total//batch_count.csv"
    )

    all_discplines = list(batch_df["discpline"])
    for discpline in all_discplines:
        extract_discpline_env(path, cpu_count, discpline)


if __name__ == "__main__":
    main()
