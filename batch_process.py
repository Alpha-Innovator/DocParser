import os
import shutil
import argparse
import multiprocessing
from typing import List
from uuid import uuid4
import pandas as pd

from vrdu import logger
from vrdu import utils
from main import process_one_file

log_file = str(uuid4()) + ".log"
log = logger.setup_app_level_logger(file_name=log_file, level="INFO")

database = "data/processed_paper_database.csv"


def filter_tex_files(tex_files: List[str], main_path: str) -> List[str]:
    """extract all MAIN.tex files for processing,
    only MAIN.tex files in the main_path (not recursive) are extracted

    Args:
        tex_files (List[str]): list of tex files
        main_path (str): path to main directory.

    Returns:
        List[str]: list of tex files that are compiable.
    """

    # TODO: move this to config
    redundant_tex_files = [
        "paper_colored.tex",
        "paper_white.tex",
        "paper_original.tex",
    ]

    result = []
    for tex_file in tex_files:
        if "paper_block_" in tex_file:
            continue

        if os.path.basename(tex_file) in redundant_tex_files:
            continue

        # ensure the tex files inside a subfolder is not included
        # ex: cs.AI/1234.4567/figs/draw.tex will be excluded
        if main_path and os.path.dirname(os.path.dirname(tex_file)) != main_path:
            continue

        # make sure the tex file is compiable (main document)
        try:
            with open(tex_file) as f:
                content = f.read()
            if "\\begin{document}" not in content:
                continue
            result.append(tex_file)
        except UnicodeDecodeError:
            log.debug(f"failed to read tex file: {tex_file} due to UnicodeDecodeError")
            continue

    # skip processed papers
    log.info(f"[VRDU] Before filtering, found {len(result)} tex files")
    if os.path.exists(database):
        df = pd.read_csv(database)
        processed_papers = set(df["path"])
        result = [x for x in result if os.path.dirname(x) not in processed_papers]

    log.info(f"[VRDU] After filtering, found {len(result)} tex files")
    return result


def process_one_discpline(path: str, cpu_count: int, discpline: str) -> None:
    """Process the data in a specific discpline.

    Args:
        path (str): The path to the raw data.
        cpu_count (int): The number of CPUs to use for multiprocessing.
        discpline (str): The discpline to process.

    Raises:
        Exception: If the processing fails.

    Returns:
        None
    """
    discpline_path = os.path.join(path, discpline)
    log.info(f"[VRDU] Path to raw data: {discpline_path}")
    log.info(f"[VRDU] Using cpu counts: {cpu_count}")
    tex_files = utils.extract_all_tex_files(discpline_path)
    tex_files = filter_tex_files(tex_files, discpline_path)

    try:
        with multiprocessing.Pool(cpu_count) as pool:
            pool.map(process_one_file, tex_files)
    except Exception:
        log.exception(f"[VRDU] discpline: {discpline}, failed to process.")
    finally:
        # save the process log
        log.info(f"[VRDU] discpline: {discpline}, finished processing.")
        shutil.move(log_file, f"data/batch_process_{discpline}.log")


def main():
    """This function is the entry point of the application.

    Args:
        path (str): The path to the raw data.
        cpu_count (int): The number of CPUs to use for multiprocessing.
        discpline (str): The discpline to process.

    Raises:
        Exception: If the processing fails.

    Returns:
        None

    References:
        https://arxiv.org/category_taxonomy
    """
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--path", type=str, required=True, help="path to raw data"
    )
    parser.add_argument(
        "-c",
        "--cpu_count",
        type=int,
        required=True,
        help="cpu count for multiprocessing",
    )
    parser.add_argument(
        "-t", "--discpline", type=str, required=True, help="discpline to process"
    )
    args = parser.parse_args()
    path, cpu_count, discpline = args.path, args.cpu_count, args.discpline

    log.info(f"[VRDU] discpline: {discpline}, start to process.")
    process_one_discpline(path, cpu_count, discpline)


if __name__ == "__main__":
    main()
