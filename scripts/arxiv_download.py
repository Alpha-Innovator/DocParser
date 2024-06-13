import arxiv
import os
from typing import List, Dict
from tqdm import tqdm
import tarfile


from DocParser.vrdu import utils
from DocParser.vrdu import logger

log = logger.setup_app_level_logger(file_name="arxiv_download.log")


def arxiv_download(data: List[Dict], path: str) -> None:
    """Download papers from arXiv based on category data.

    This function takes a list of category download tasks and a base
    path. For each category item in the data, it will:

    1. Create a subdirectory under the given path for that category
    2. Check if there are already enough papers in the subdir
    3. Search arXiv for the category
    4. Download up to the requested count of newest papers
    5. Save each paper to the category subdirectory

    Arguments:
        data (List[Dict]): List of dicts with keys "category" and "count"
        path (str): Base directory path to save papers

    Returns:
        None
    """
    client = arxiv.Client()
    for row in tqdm(data):
        if row["auto_annotated_paper_path"]:
            continue
        discipline = row["discipline"]
        discipline_path = os.path.join(path, discipline)
        os.makedirs(discipline_path, exist_ok=True)

        if os.path.exists(os.path.join(discipline_path, row["paper_id"])):
            log.debug(f'{os.path.join(discipline_path, row["paper_id"])} exists')
            continue

        if os.path.exists(os.path.join(discipline_path, row["paper_id"], ".tar.gz")):
            log.debug(
                f'{os.path.join(discipline_path, row["paper_id"], ".tar.gz")} exists'
            )
            continue

        search_results = client.results(arxiv.Search(id_list=[row["paper_id"]]))

        for result in search_results:
            tar_file_path = result.download_source(dirpath=discipline_path)
            log.debug(f"Downloading tar file {tar_file_path}")
            paper_path = os.path.join(discipline_path, row["paper_id"])
            try:
                with tarfile.open(tar_file_path, "r:gz") as tar:
                    tar.extractall(paper_path)
            except tarfile.ReadError:
                log.error(f"{tar_file_path} is not a tar.gz file")
                continue


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--path", type=str, required=True, help="Path to save result"
    )
    parser.add_argument(
        "-f", "--file", type=str, required=True, help="json file for saving result"
    )

    args = parser.parse_args()
    output_path, json_file = args.path, args.file

    json_data = utils.load_json(json_file)

    arxiv_download(json_data, output_path)


if __name__ == "__main__":
    main()
