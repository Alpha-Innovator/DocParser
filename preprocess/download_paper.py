import arxiv
import os
from typing import List, Dict


def arxiv_download(data: List[Dict], path: str):
    for row in data:
        category, count = row["categories"], int(row["count"])
        sub_directory = os.path.join(path, category)
        os.makedirs(sub_directory, exist_ok=True)

        if len(os.listdir(sub_directory)) >= count:
            continue

        search = arxiv.Search(
            query=category,
            max_results=count,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        for result in search.results():
            result.download_source(dirpath=sub_directory)
