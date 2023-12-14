import os
import shutil
import uuid
import datetime

from vrdu import utils
from vrdu.config import config


def extract_category(path, category, output_path):
    source_json_file = os.path.join(path, "reading_annotation.json")
    data = utils.load_json(source_json_file)

    result = []

    for key, blocks in data.items():
        # x must be page index
        if not key.isnumeric():
            continue
        for block in blocks:
            if "category" not in block:
                return
            if block["category"] == category:
                result.append(block)

    for key in result:
        output_image_name = f"{uuid.uuid4()}.png"
        shutil.copyfile(
            os.path.join(path, key["image_path"]),
            os.path.join(output_path, output_image_name),
        )
        key["image_path"] = output_image_name
        key["paper_source"] = path
        key["added_date"] = str(datetime.date.today())

    return result


def main(category_name, input_directory, output_path):
    """extract all blocks that is of the given category to a given output directory"""
    if category_name not in config.name2category.keys():
        raise KeyError(
            f"Unknown category name, avalaible category names: {list(config.name2category.keys())}"
        )

    category = config.name2category[category_name]
    result_json = os.path.join(output_path, "reading_annotation.json")

    existed_source = set()
    if os.path.exists(result_json):
        existed_source = set(
            item["paper_source"] for item in utils.load_json(result_json)
        )

    count = 0
    for root, dirs, files in os.walk(input_directory):
        if "reading_annotation.json" not in files:
            continue

        # if data of this folder has been extracted
        if root in existed_source:
            continue

        count += 1

        print(f"extract data from {root} to {output_path}")
        extract_category(root, category, output_path)

    # exclude the reading_annotation.json file
    num_of_samples = len(os.listdir(output_path)) - 1
    print(f"extracted {count} files, {num_of_samples} samples obtained.")


if __name__ == "__main__":
    category_name = "Equation"
    input_directory = os.path.expanduser("/cpfs01/shared/ADLab/datasets/vrdu_arxiv")
    output_path = os.path.expanduser(
        f"/cpfs01/shared/ADLab/datasets/vrdu_{category_name.lower()}"
    )

    main(category_name, input_directory, output_path)
