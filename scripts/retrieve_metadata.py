import glob
import os
from pathlib import Path
from typing import Any, Dict, List
import arxiv
import argparse


from DocParser.vrdu import utils
from DocParser.logger import logger

log = logger.setup_app_level_logger(file_name="retrieve_metadata.log")


def retrieve_metadata(data: Dict[str, Path], slice_length=100) -> List[Dict[str, Any]]:
    """
    Retrieves metadata for the given list of paper IDs.

    Args:
    data (Dict[str, Path]): A dictionary where keys are paper IDs and values are the paths to the corresponding papers.
    slice_length (int, optional): The number of paper IDs to retrieve metadata for in each iteration. Defaults to 100.

    Returns:
    List[Dict[str, Any]]: A list of dictionaries containing metadata for each paper.

    Raises:
    None

    References:
    https://info.arxiv.org/help/api/user-manual.html#_details_of_atom_results_returned

    """
    paper_ids = list(data.keys())

    client = arxiv.Client()

    paper_metadata = []

    for i in range(len(paper_ids), slice_length):
        slices = paper_ids[i : i + slice_length]
        search_results = client.results(arxiv.Search(id_list=slices))

        for index, result in enumerate(search_results):
            paper_metadata.append(
                {
                    "entry_id": result.entry_id,
                    "updated": str(result.updated),
                    "published": str(result.published),
                    "title": result.title,
                    "doi": result.doi,
                    "authors": [str(author) for author in result.authors],
                    "summary": result.summary,
                    "journal_ref": result.journal_ref,
                    "primary_category": result.primary_category,
                    "categories": result.categories,
                    "links": [str(link) for link in result.links],
                    "pdf_url": result.pdf_url,
                    "paper_id": slices[index],
                    "paper_path": data[slices[index]],
                    "quality": "low",
                }
            )

    return paper_metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_path", type=str, required=True)
    args = parser.parse_args()
    path = args.input_path

    paper_paths = glob.glob(os.path.join(path, "*/"))
    # paper_id to paper path
    data = {os.path.basename(paper_path[:-1]): paper_path for paper_path in paper_paths}

    paper_metadata = retrieve_metadata(data)

    # use append mode
    existed_json_file = os.path.join(path, "paper_metadata.json")
    existed_json_data = []
    if os.path.exists(existed_json_file):
        existed_json_data = utils.load_json(existed_json_file)

    existed_paper_ids = [x["paper_id"] for x in existed_json_data]
    existed_json_data.extend(
        [x for x in paper_metadata if x["paper_id"] not in existed_paper_ids]
    )

    utils.export_to_json(existed_json_data, existed_json_file)


if __name__ == "__main__":
    main()
