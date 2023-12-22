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

layout_keys = [
    "columnwidth",
    "columnsep",
    "textwidth",
    "paperwidth",
    "hoffset",
    "voffset",
    "oddsidemargin",
    "evensidemargin",
    "marginparwidth",
    "marginparsep",
    "topmargin",
    "headheight",
    "headsep",
    "footskip",
    "textheight",
]


relation_map = {
    ("Text", "Text"): "adj",
    ("Text", "Text-EQ"): "adj",
    ("Text", "Equation"): "adj",
    ("Text", "List"): "adj",
    ("Text", "Footnote"): "ref",
    ("Text-EQ", "Text"): "adj",
    ("Text-EQ", "Text-EQ"): "adj",
    ("Text-EQ", "Equation"): "adj",
    ("Text-EQ", "List"): "adj",
    ("Text-EQ", "Footnote"): "ref",
    ("Equation", "Text"): "adj",
    ("Equation", "Text-EQ"): "adj",
    ("Equation", "Equation"): "adj",
    ("Equation", "List"): "adj",
    ("Equation", "Footnote"): "ref",
    ("List", "Text"): "adj",
    ("List", "Text-EQ"): "adj",
    ("List", "Equation"): "adj",
    ("List", "List"): "adj",
    ("List", "Footnote"): "ref",
    ("Title", "Text"): "sub",
    ("Title", "Text-EQ"): "sub",
    ("Title", "Equation"): "sub",
    ("Title", "List"): "sub",
    ("Title", "Footnote"): "ref",
    # Title category relationships
    ("chapter", "chapter"): "peer",
    ("section", "chapter"): "sub",
    ("section", "section"): "peer",
    ("subsection", "section"): "sub",
    ("subsection", "subsection"): "peer",
    ("subsubsection", "subsection"): "sub",
    ("subsubsection", "subsubsection"): "peer",
}

sortable_envs = [
    "Title",
    "Text",
    "Text-EQ",
    "Equation",
    "Footnote",
    "List",
    "PaperTitle",
    "Abstract",
]


sortable_envs = ["Title", "Text", "Text-EQ", "Equation", "Footnote", "List"]


threshold = 0.3
ppi = 72
prefix = "block_"
