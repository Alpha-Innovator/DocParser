import panel as pn
import os
import glob
from PIL import Image, ImageDraw

from DocParser.vrdu import utils
from DocParser.vrdu.config import config

pn.extension()


data_path = (
    "/cpfs01/shared/ADLab/ADLab_hdd/vrdu_arxiv/vrdu_autolabel_final_3_120w/nlin.AO"
)
default_path = os.path.expanduser(
    "/cpfs01/shared/ADLab/ADLab_hdd/vrdu_arxiv/vrdu_autolabel_final_3_120w/nlin.AO/0809.2301"
)

# get all renderable paper paths
paper_paths = []
for root, dirs, files in os.walk(data_path):
    if "order_annotation.json" in files:
        paper_paths.append(root)

# generate select widget from paper paths
paper_select = pn.widgets.Select(value=default_path, options=paper_paths)

# load layout info from a given paper
layout_info = utils.load_json(os.path.join(default_path, "order_annotation.json"))
layout_info = layout_info["annotations"]

# get all image paths of a given paper
image_paths = sorted(glob.glob(os.path.join(default_path, "original-page-*.jpg")))

# generate select widget from image paths
image_select = pn.widgets.Select(value=image_paths[0], options=image_paths)
image_pane = pn.pane.PNG()
image_pane.height = 800
image_pane.width = 600

# generate pane to display source code
source_code_pane = pn.Column("# Source Code")

# generate select widget to show annotations of different categories
category_select = pn.widgets.Select(
    value="All", options=["All"] + list(config.name2category.keys())
)


@pn.depends(paper_select.param.value)
def update_paper(path):
    global layout_info
    layout_info = utils.load_json(os.path.join(path, "order_annotation.json"))
    layout_info = layout_info["annotations"]
    image_paths = sorted(glob.glob(os.path.join(path, "original-page-*.jpg")))
    image_select.options = image_paths


@pn.depends(image_select.param.value)
def update_image(image_path):
    image = Image.open(image_path)
    image_pane.object = image
    image_pane.width = image.size[0]
    image_pane.height = image.size[1]


@pn.depends(image_select.param.value, category_select.param.value)
def update_annotation(image_path, category):
    if not image_path:
        return
    source_code_pane.clear()
    source_code_pane.append("# Source Code")
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    image_id = int(os.path.splitext(os.path.basename(image_path))[0][-4:])
    print(f"image_id={image_id}")

    # filter blocks
    if category == "All":
        print(layout_info)
        blocks = [block for block in layout_info if block["page_index"] == image_id]
    else:
        blocks = [
            block
            for block in layout_info
            if block["page_index"] == image_id
            if block["category"] == config.name2category[category]
        ]

    for index, block in enumerate(blocks):
        bbox = (
            block["bbox"][0],
            block["bbox"][1],
            block["bbox"][2],
            block["bbox"][3],
        )
        draw.rectangle(bbox, outline="red", width=3)
        if block["parent_block"] is None:
            source_code_pane.append("* " + block["source_code"])

    image_pane.object = image


app = pn.Row(
    image_pane,
    pn.Column(
        pn.Row("# Paper", paper_select),
        pn.Row("# Image", image_select),
        pn.Row("# Category", category_select),
        source_code_pane,
    ),
    update_paper,
    update_image,
    update_annotation,
)

app.servable()

# use the following command to visualize
# panel serve app.py --show --autoreload
