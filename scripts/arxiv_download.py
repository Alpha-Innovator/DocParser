import argparse
import arxiv
import os
from typing import List
import tarfile


from vrdu import logger


log = logger.setup_app_level_logger(logger_name="arxiv_download.log")


def download_papers_with_paper_id(
    path: str, discipline: str, paper_ids: List[str]
) -> None:
    """
    Downloads papers from the Arxiv repository based on the specified paper IDs.

    Args:
    - path (str): The path where the downloaded papers will be saved.
    - discipline (str): The discipline of the papers to be downloaded.
    - paper_ids (List[str]): A list of paper IDs to be downloaded.

    Returns:
    None

    Raises:
    - tarfile.ReadError: cannot unpack the .tar.gz file

    Usage:
    ```python
    download_papers_with_paper_id(path, discipline, paper_ids)
    ```

    """
    client = arxiv.Client()
    discipline_path = os.path.join(path, discipline)
    os.makedirs(discipline_path, exist_ok=True)

    search_results = client.results(arxiv.Search(id_list=paper_ids))

    for result in search_results:
        # extract {id} without version from http://arxiv.org/abs/{id}
        paper_id = result.entry_id.split("/")[1].split("v")[0]
        log.info(f"Downloading paper {paper_id}")

        tar_file_path = result.download_source(dirpath=discipline_path)
        log.info(f"Downloading tar file {tar_file_path}")
        paper_path = os.path.join(discipline_path, paper_id)
        if os.path.exists(paper_path):
            continue

        try:
            with tarfile.open(tar_file_path, "r:gz") as tar:
                tar.extractall(paper_path)
        except tarfile.ReadError:
            log.error(f"{tar_file_path} is not a tar.gz file")
            continue


def download_batch_papers(path: str, discipline: str, num_papers: int) -> None:
    """
    Downloads a batch of papers from the Arxiv repository
    based on the specified discipline and number of papers.

    Args:
    - path (str): The path where the downloaded papers will be saved.
    - discipline (str): The discipline of the papers to be downloaded.
    - num_papers (int): The number of papers to be downloaded.

    Returns:
    None

    Raises:
    None

    Usage:
    ```python
    download_batch_papers(output_path, discipline, num_papers)
    ```

    """
    client = arxiv.Client()

    paper_ids = []
    while num_papers > 0:
        search_results = client.results(
            arxiv.Search(query=discipline, max_results=num_papers)
        )

        for result in search_results:
            paper_id = result.entry_id.split("/")[1].split("v")[0]
            log.debug(f"Downloading paper {paper_id}")
            if paper_id not in paper_ids:
                paper_ids.append(paper_id)
                num_papers -= 1

    download_papers_with_paper_id(path, discipline, paper_ids)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--path", type=str, required=True, help="Path to save result"
    )
    parser.add_argument(
        "-d", "--discipline", type=str, default="cs.CV", help="discipline to download"
    )
    parser.add_argument(
        "-i", "--num_papers", type=int, default=1, help="Number of paper to download"
    )

    args = parser.parse_args()
    output_path, discipline, num_papers = args.path, args.discipline, args.num_papers

    download_batch_papers(output_path, discipline, num_papers)


if __name__ == "__main__":
    main()
