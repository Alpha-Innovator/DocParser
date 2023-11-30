import os
import json

dirname = os.path.dirname(__file__)
file_path = os.path.join(dirname, "config.json")

with open(file_path, "r") as json_file:
    config = json.load(json_file)

category2name = {category: name for category, name, _ in config["category_name"]}
name2category = {name: category for category, name, _ in config["category_name"]}
name2rgbcolor = {name: tuple([0, 0, 0]) for name in name2category.keys()}
name2color = {name: name + "_color" for name in name2category.keys()}

# used to annotate the object detection result
colors_map = config["annotation_color"]
