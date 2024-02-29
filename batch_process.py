import os
import shutil
import argparse
import multiprocessing
from typing import List
from uuid import uuid4

from vrdu import logger
from vrdu import utils
from main import process_one_file

log_file = str(uuid4()) + ".log"
log = logger.setup_app_level_logger(file_name=log_file, level="INFO", mode="a")


def filter_tex_files(tex_files: List[str], main_path: str = None) -> List[str]:
    """extract all MAIN.tex files for processing, if main_path is not None, then
    only extract MAIN.tex files in the main_path (not recursive)

    Args:
        tex_files (List[str]): list of tex files
        main_path (str, optional): path to main directory. Defaults to None.

    Returns:
        List[str]: list of tex files that are compiable.
    """
    result = []
    for tex_file in tex_files:
        if main_path and os.path.dirname(os.path.dirname(tex_file)) != main_path:
            continue
        # prevent processing previous generated files
        try:
            with open(tex_file) as f:
                content = f.read()
            if "\\begin{document}" not in content:
                continue
            result.append(tex_file)
        except UnicodeDecodeError:
            log.debug(f"failed to read tex file: {tex_file}")
            continue

    return result


def process_one_category(path, cpu_count, category):
    category_path = os.path.join(path, category)
    log.info(f"path to raw data: {category_path}")
    log.info(f"Using cpu counts: {cpu_count}")
    tex_files = utils.extract_all_tex_files(category_path)
    tex_files = filter_tex_files(tex_files, category_path)
    log.info(f"Found {len(tex_files)} tex files")

    try:
        with multiprocessing.Pool(cpu_count) as pool:
            pool.map(process_one_file, tex_files)
        # save log file
    except Exception:
        log.exception(f"[VRDU] category: {category}, failed to process.")
    finally:
        # save the process log
        shutil.move(log_file, f"batch_process_{category}.log")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, required=True)
    parser.add_argument("-c", "--cpu_count", type=int, required=True)
    parser.add_argument("-t", "--category", type=str, required=False)
    args = parser.parse_args()
    path, cpu_count, category = args.path, args.cpu_count, args.category

    categories = [category] if category is not None else utils.get_all_categories()

    for category in categories:
        log.info(f"Processing single category: {category}")
        process_one_category(path, cpu_count, category)
