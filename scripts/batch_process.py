import os
import argparse
import multiprocessing
import shutil
from typing import List
import pandas as pd

from DocParser.logger import logger
from DocParser.main import process_one_file

log = logger.setup_app_level_logger(file_name="batch_process.log", level="INFO")


def filter_tex_files(discipline_path: str) -> List[str]:
    """
    Filters the list of tex files in the given discipline path.

    Args:
        discipline_path (str): The path to the discipline directory containing tex files.

    Returns:
        List[str]: A list of filtered tex files that meet the specified criteria.

    Raises:
        Exception: If the processing fails.

    1. Exclude tex files with names "paper_colored.tex", "paper_white.tex", and "paper_original.tex".
    2. Exclude tex files that are inside a subfolder.
    3. Ensure that the tex file is a main document by checking if it contains "\\begin{document}".

    """
    tex_files = []

    for root, _, files in os.walk(discipline_path):
        tex_files.extend(
            [os.path.join(root, file) for file in files if file.endswith(".tex")]
        )

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
        if os.path.dirname(os.path.dirname(tex_file)) != discipline_path:
            continue

        # make sure the tex file is compilable (main document)
        try:
            with open(tex_file) as f:
                content = f.read()
            if "\\begin{document}" not in content:
                continue
            result.append(tex_file)
        except UnicodeDecodeError:
            log.debug(f"failed to read tex file: {tex_file} due to UnicodeDecodeError")
            continue

    return result


def process_one_discipline(path: str, cpu_count: int, discipline: str) -> None:
    """Process the data in a specific discipline.

    Args:
        path (str): The path to the raw data.
        cpu_count (int): The number of CPUs to use for multiprocessing.
        discipline (str): The discipline to process.

    Raises:
        Exception: If the processing fails.

    Returns:
        None
    """
    discipline_path = os.path.join(path, discipline)
    log.info(f"[VRDU] Path to raw data: {discipline_path}")
    log.info(f"[VRDU] Using cpu counts: {cpu_count}")
    tex_files = filter_tex_files(discipline_path)

    try:
        with multiprocessing.Pool(cpu_count) as pool:
            pool.map(process_one_file, tex_files)
    except Exception:
        log.exception(f"[VRDU] discipline: {discipline}, failed to process.")
    finally:
        # save the process log
        log.info(f"[VRDU] discipline: {discipline}, finished processing.")


def main():
    """This function is the entry point of the application.

    Args:
        path (str): The path to the raw data.
        cpu_count (int): The number of CPUs to use for multiprocessing.
        discipline (str): The discipline to process.

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
        "-t", "--discipline", type=str, required=True, help="discipline to process"
    )
    args = parser.parse_args()
    path, cpu_count, discipline = args.path, args.cpu_count, args.discipline

    log.info(f"[VRDU] discipline: {discipline}, start to process.")
    process_one_discipline(path, cpu_count, discipline)


if __name__ == "__main__":
    main()
