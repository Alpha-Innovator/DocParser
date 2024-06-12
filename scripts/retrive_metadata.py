import glob
import os
from typing import Any, Dict, List
import arxiv
import argparse

import pandas as pd


from vrdu import utils
from vrdu import logger

log = logger.setup_app_level_logger(file_name="retrieve_metadata.log")


def retrieve_metadata(data: Dict) -> List[Dict[str, Any]]:
    paper_ids = list(data.keys())

    client = arxiv.Client()

    slice_length = 100
    paper_metadata = []

    for i in range(0, len(paper_ids), slice_length):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input_path", type=str, default="data/discipline_info.csv"
    )
    args = parser.parse_args()
    path = args.input_path

    discipline_info = pd.read_csv("data/discipline_info.csv")
    disciplines = set(discipline_info["discipline"])

    for discipline in disciplines:
        target_discipline_path = os.path.join(path, discipline)
        paper_paths = glob.glob(os.path.join(target_discipline_path, "*/"))

        data = {
            os.path.basename(paper_path[:-1]): paper_path for paper_path in paper_paths
        }

        paper_metadata = retrieve_metadata(data)

        existed_json_file = os.path.join(target_discipline_path, "paper_metadata.json")
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
