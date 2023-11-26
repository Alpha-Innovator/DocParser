import os
import shutil
import uuid

from vrdu import utils
from vrdu.config import config


def extract_category(path, category_name, output_path):
    print(f"extract category {category_name} from {path} to {output_path}")
    json_file = os.path.join(path, "reading_annotation.json")
    data = utils.load_json(json_file)

    category = config.name2category[category_name]
    result_json = os.path.join(output_path, "reading_annotation.json")

    result = []

    for x, pairs in data.items():
        if not x.isnumeric():
            continue
        for p in pairs:
            if "category" not in p:
                return
            if p["category"] == category:
                result.append(p)

    for x in result:
        output_image_name = f"{uuid.uuid4()}.png"
        shutil.copyfile(
            os.path.join(path, x["image_path"]),
            os.path.join(output_path, output_image_name),
        )
        x["image_path"] = output_image_name

    if os.path.exists(result_json):
        data = utils.load_json(result_json)
        result.extend(data)

    utils.export_to_json(result, result_json)


if __name__ == "__main__":
    directory = os.path.expanduser("/home/PJLAB/maosong/vrdu_data")
    for root, dirs, files in os.walk(directory):
        if "reading_annotation.json" not in files:
            continue

        category_name = "Table"
        output_path = os.path.expanduser(f"~/Desktop/sample_data/{category_name}")
        extract_category(root, category_name, output_path)
