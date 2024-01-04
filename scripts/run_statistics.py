from collections import defaultdict
import os
from typing import Dict
import csv

from vrdu import utils


def is_standalone(path: str) -> bool:
    with open(path, "r") as f:
        content = f.read()
    return "standalone" in content


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
    standalone_files = []
    others = []

    for tex_file in all_tex_files:
        root = os.path.dirname(tex_file)
        category = os.path.dirname(root).split("/")[-1]
        if category not in all_categories:
            if is_standalone(tex_file):
                standalone_files.append(tex_file)
            else:
                others.append(tex_file)
        elif os.path.exists(os.path.join(root, "output/result/quality_report.json")):
            success_files[category].append(tex_file)

        total_files[category].append(tex_file)

    data = {
        "main": {
            category: {
                "total": total_files[category],
                "successed": success_files[category],
                "rate": (len(success_files[category]) / len(total_files[category]))
                * 100,
            }
            for category in total_files
        },
        "standalone": standalone_files,
        "others": others,
    }

    return data


if __name__ == "__main__":
    data = analyze_result("/cpfs01/shared/ADLab/datasets/vrdu_arxiv")
    categories = utils.get_all_categories()
    with open("statistics.csv", "w") as f:
        fieldnames = ["category", "total", "successed"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in categories:
            writer.writerow(
                {
                    "category": key,
                    "total": len(data["main"][key]["total"]),
                    "successed": len(data["main"][key]["successed"]),
                }
            )
    utils.export_to_json(data, "result_statistics.json")
