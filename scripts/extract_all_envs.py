import argparse
import multiprocessing
import os
import re
from typing import List
import pandas as pd


from vrdu import utils
from vrdu import logger

known_envs = [
    "document",
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "flalign",
    "falign*",
    "multiline",
    "multiline*",
    "alignat",
    "alignat*",
    "split",
    "eqnarray",
    "eqnarray*",
    "tabular",
    "tabular*",
    "tabularx",
    "tabulary",
    "longtable",
    "tabu",
    "longtabu",
    "figure",
    "minipage",
    "subfigure",
    "subfigure*",
    "tikzpicture",
    "algorithm",
    "algorithm*",
    "algorithmic",
    "algorithmic*",
    "program",
    "verbatim",
    "verbatim*",
    "lstlisting",
    "lstinputlisting",
    "itemize",
    "enumerate",
    "description",
    "theorem",
    "definition",
    "lemma",
    "remark",
    "corollary",
    "proposition",
    "example",
    "proof",
]


log = logger.setup_app_level_logger(file_name="extract_all_envs.log", mode="a")


def process_one_file(tex_file) -> List[str]:
    result = []
    try:
        with open(tex_file) as f:
            tex_content = f.read()
        pattern = r"\\begin{([^}]+)}"
        envs = re.findall(pattern, tex_content)
        result = [env for env in envs if env not in known_envs]

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

            # filter all empty items
        results = [x for result in results for x in result]

        # use append mode to update json file
        json_data = []
        if os.path.exists(json_file):
            json_data = utils.load_json(json_file)

        json_data.extend(results)
        json_data = list(set(json_data))
        utils.export_to_json(json_data, json_file)

        log.info(f"processed {i,i + batch_size}-th batch")


def extract_discpline_env(path, cpu_count, discpline):
    log.info(f"processing discpline: {discpline}")
    discpline_path = os.path.join(path, discpline)
    tex_files = utils.extract_all_tex_files(discpline_path)
    log.info(f"there are {len(tex_files)} tex_files")
    json_file = f"envs_{discpline}.json"
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
