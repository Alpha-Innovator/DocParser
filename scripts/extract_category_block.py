import os
import shutil

from vrdu import utils
from vrdu.config import config


def extract_category(path, category_name, output_path):
    json_file = os.path.join(path, "reading_annotation.json")
    data = utils.load_json(json_file)

    category = config.name2category[category_name]
    result = []
    for x, pairs in data.items():
        if not x.isnumeric():
            continue
        for p in pairs:
            if p["category"] == category:
                result.append(p)

    for x in result:
        shutil.copyfile(
            os.path.join(path, x["image_path"]),
            os.path.join(output_path, x["image_path"]),
        )

    result.append(data["categories"])
    utils.export_to_json(result, os.path.join(output_path, "reading_annotation.json"))


if __name__ == "__main__":
    path = os.path.expanduser("~/icml2022/output/result")
    category_name = "Table"
    output_path = os.path.expanduser(f"~/Desktop/sample_data/{category_name}")
    extract_category(path, category_name, output_path)
