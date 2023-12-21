from collections import defaultdict
import os
from typing import Dict, List
from rich import print

from vrdu import utils


def analyze_result(path) -> Dict:
    """
    Analyzes the processed result of the given path. This is done by checking if the
    result files exist.

    Args:
        path (str): The path to the directory containing the result files.

    Returns:
        Dict: A dictionary containing the statistics for each category.

    Raises:
        None.
    """
    all_tex_files = utils.extract_tex_files(path)
    all_categories = utils.get_all_categories()

    success_files = defaultdict(list)
    total_files = defaultdict(list)

    for tex_file in all_tex_files:
        root = os.path.dirname(tex_file)
        category = os.path.dirname(root).split("/")[-1]
        if category not in all_categories:
            continue
        if os.path.exists(os.path.join(root, "output/result/quality_report.json")):
            success_files[category].append(tex_file)

        total_files[category].append(tex_file)

    data = {
        category: {
            "successed": len(success_files[category]),
            "total": len(total_files[category]),
            "rate": (len(success_files[category]) / len(total_files[category])) * 100,
        }
        for category in total_files
    }

    utils.export_to_json(data, "result_statistics.json")

    return data


def analyze_raw_data(path):
    all_categories = utils.get_all_categories()

    data = defaultdict(int)
    for category in all_categories:
        if os.path.exists(os.path.join(path, category)):
            data[category] = len(os.listdir(os.path.join(path, category)))

    return data


data = analyze_result("/cpfs01/shared/ADLab/datasets/vrdu_arxiv")
