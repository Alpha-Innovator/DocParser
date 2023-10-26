import os
import json
import cv2
import numpy as np

file_path = os.path.expanduser("config/config.json")

with open(file_path, "r") as json_file:
    config = json.load(json_file)

category2name = {k: v for k, v in config["category_name"]}
name2category = {name: category for category, name in config["category_name"]}
category2rgbcolor = {
    category: tuple(color) for category, color in config["category_color"]
}
name2rgbcolor = {
    name: category2rgbcolor[category] for name, category in name2category.items()
}
category2color = {k: v for k, v in config["category_color"]}


category2hsv_bound = {}  # category: (lower_bound, upper_bound)
for k, v in category2color.items():
    rgb_color = tuple(v)

    # Convert RGB to HSV
    hsv_color = cv2.cvtColor(np.uint8([[rgb_color]]), cv2.COLOR_RGB2HSV)[0][0]

    lower_bound = np.array(
        [
            hsv_color[0] - config["hue_range"],
            hsv_color[1] - config["saturation_range"],
            hsv_color[2] - config["value_range"],
        ]
    )
    upper_bound = np.array(
        [
            hsv_color[0] + config["hue_range"],
            hsv_color[1] + config["saturation_range"],
            hsv_color[2] + config["value_range"],
        ]
    )

    category2hsv_bound[k] = (lower_bound, upper_bound)
