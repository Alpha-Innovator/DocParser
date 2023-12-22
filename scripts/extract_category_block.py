import os
import shutil
import subprocess
import uuid
import datetime
import re
import glob

from vrdu import utils
from vrdu.config import config


def is_standalone(file_path):
    try:
        with open(file_path, "r") as f:
            file_content = f.read()
    except UnicodeDecodeError:
        return False
    pattern = r"\\documentclass(\[.*\])?\{standalone\}"
    return bool(re.search(pattern, file_content))


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


def extract_tikz(path, output_path):
    # FIXME: problem exists, do not use it before this function get fixes
    json_data = utils.load_json("result_statistics.json")
    result = [x for x in json_data["standalone"] if is_standalone(x)]
    print(f"Found {len(result)} standalone files")

    data = []
    original_path = os.getcwd()
    try:
        os.chdir(output_path)
        for tex_file in result:
            base_name = str(uuid.uuid4())
            output_tex_name = os.path.join(output_path, f"{base_name}.tex")
            print(f"moving {tex_file} to {output_tex_name}")
            shutil.copyfile(tex_file, os.path.join(output_path, output_tex_name))
            subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex_name])
            subprocess.run(
                [
                    "convert",
                    "-density",
                    "300",
                    base_name + ".pdf",
                    "-quality",
                    "90",
                    base_name + ".png",
                ]
            )
            print("converted")
            data.append(
                {
                    "image_path": [],
                    "source_code": output_tex_name,
                    "data_source": tex_file,
                }
            )

    except Exception:
        pass
    finally:
        os.chdir(original_path)
        utils.export_to_json(data, os.path.join(output_path, "tikz_annotation.json"))


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
    # output_path = os.path.expanduser(
    #     f"/cpfs01/shared/ADLab/datasets/vrdu_{category_name.lower()}"
    # )

    # main(category_name, input_directory, output_path)
    output_path = "/cpfs01/shared/ADLab/datasets/vrdu_tikz"
    extract_tikz(input_directory, output_path)
