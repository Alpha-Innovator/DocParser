import arxiv
import os
from typing import List, Dict
from tqdm import tqdm
import tarfile
import csv
import random


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
    for row in tqdm(data):
        category, count = row["categories"], int(row["count"])
        print(f"category: {category}, count: {count}")
        sub_directory = os.path.join(path, category)
        os.makedirs(sub_directory, exist_ok=True)

        search = arxiv.Search(
            query=category,
            max_results=count,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        for result in search.results():
            file_name = result._get_default_filename()
            if os.path.exists(os.path.join(sub_directory, file_name)):
                continue
            
            result.download_source(dirpath=sub_directory)


def extract_all_tar_gz(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.endswith(".tar.gz"):
                continue
            file_path = os.path.join(root, file)
            extract_path = os.path.splitext(file_path)[0]
            extract_path = os.path.splitext(extract_path)[0]
            if os.path.exists(extract_path):
                continue
            extract_tar_gz(file_path, extract_path)


def extract_tar_gz(file_path, extract_path):
    with tarfile.open(file_path, "r:gz") as tar:
        tar.extractall(extract_path)


if __name__ == "__main__":
    path = os.path.expanduser("/cpfs01/shared/ADLab/datasets/vrdu_arxiv")
    data = []
    with open("scripts/category_count.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    random.shuffle(data)
    arxiv_download(data=data, path=path)
    for root, dirs, files in os.walk(path):
        for dir_ in dirs:
            extract_all_tar_gz(os.path.join(root, dir_))
