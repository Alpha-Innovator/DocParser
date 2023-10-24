import arxiv
import os
from typing import List, Dict


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
