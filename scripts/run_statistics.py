from collections import defaultdict
import os
import re
from rich import print

from vrdu.utils import get_all_categories


def analyze_result():
    success_counts = defaultdict(int)
    failure_counts = defaultdict(int)

    with open("success_files.txt", "r") as f:
        for line in f:
            category = re.match(
                r"/cpfs01/shared/ADLab/datasets/vrdu_arxiv/(.*?)/", line
            ).group(1)
            success_counts[category] += 1

    with open("failed_files.txt", "r") as f:
        for line in f:
            category = re.match(
                r"/cpfs01/shared/ADLab/datasets/vrdu_arxiv/(.*?)/", line
            ).group(1)
            failure_counts[category] += 1

    total_counts = defaultdict(int)

    for category, count in success_counts.items():
        total_counts[category] = success_counts[category] + failure_counts[category]

    for category, count in failure_counts.items():
        total_counts[category] = success_counts[category] + failure_counts[category]

    data = {
        category: (success_counts[category] / total_counts[category]) * 100
        for category in total_counts
    }

    return data


def analyze_raw_data(path):
    categories = get_all_categories()

    data = defaultdict(int)
    for category in categories:
        if os.path.exists(os.path.join(path, category)):
            data[category] = len(os.listdir(os.path.join(path, category)))

    return data


data = analyze_raw_data(
    "/cpfs01/shared/ADLab/datasets/arxiv_source/arxiv_source_uncompressed"
)

print(f"sum of data: {sum(data.values())}")

print({k: v for k, v in data.items() if k.startswith("cs")})
print(
    f"sum of cs: {sum({k: v for k, v in data.items() if k.startswith('cs')}.values())}"
)
