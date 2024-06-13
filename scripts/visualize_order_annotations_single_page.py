import argparse
from collections import defaultdict
import math
import os
from typing import Tuple
from PIL import Image, ImageDraw
from matplotlib import pyplot as plt

from DocParser.vrdu import utils


def arrowedLine(
    image: Image.Image,
    point_A: Tuple[float, float],
    point_B: Tuple[float, float],
    width=1,
    color=(0, 255, 0),
) -> Image.Image:
    """Draw a line from point_A to point_B with an arrow headed at ppoint_B."""
    draw = ImageDraw.Draw(image)
    draw.line((point_A, point_B), width=width, fill=color)

    # Calculate arrowhead vertices
    x0, y0 = point_A
    x1, y1 = point_B
    xb = 0.95 * (x1 - x0) + x0
    yb = 0.95 * (y1 - y0) + y0
    alpha = math.atan2(y1 - y0, x1 - x0) - 90 * math.pi / 180
    a = 8 * math.cos(alpha)
    b = 8 * math.sin(alpha)
    vtx0 = (xb + a, yb + b)
    vtx1 = (xb - a, yb - b)

    # Draw the arrowhead triangle
    draw.polygon([vtx0, vtx1, point_B], fill=color)
    return image


def visualize_order_annotation_single_page(path: str, page_index: int) -> None:
    order_annotation_file = os.path.join(path, "order_annotation.json")
    image_file = os.path.join(path, f"page_{page_index:04}.jpg")

    # extract blocks in this page
    order_annotation_data = utils.load_json(order_annotation_file)
    page_blocks = defaultdict(list)
    id2blocks = {}
    page2id2 = defaultdict(list)
    for block in order_annotation_data["annotations"]:
        page_blocks[block["page_index"]].append(block)
        id2blocks[block["block_id"]] = block
        page2id2[block["page_index"]].append(block["block_id"])

    page_relations = []
    for item in order_annotation_data["orders"]:
        if item["from"] not in page2id2[page_index]:
            continue
        if item["to"] not in page2id2[page_index]:
            continue
        page_relations.append(item)

    # visualize
    image = Image.open(image_file)
    width, height = image.size

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(16, 20), gridspec_kw={"height_ratios": [5, 1]}
    )
    ax1.imshow(image, extent=[0, width, height, 0])
    ax1.set_xlim(0, width)
    ax1.set_ylim(height, 0)
    color_map = {
        "identical": "green",
        "adj": "blue",
        "peer": "red",
        "implicit-cite": "purple",
        "explicit-cite": "brown",
        "sub": "orange",
        "unknown": "black",
    }

    for relation in page_relations:
        print(relation)
        block_from = id2blocks[relation["from"]]
        block_to = id2blocks[relation["to"]]
        center_from = (
            (block_from["bbox"][0] + block_from["bbox"][2]) / 2,
            (block_from["bbox"][1] + block_from["bbox"][3]) / 2,
        )
        center_to = (
            (block_to["bbox"][0] + block_to["bbox"][2]) / 2,
            (block_to["bbox"][1] + block_to["bbox"][3]) / 2,
        )
        ax1.arrow(
            center_from[0],
            center_from[1],
            center_to[0] - center_from[0],
            center_to[1] - center_from[1],
            fc=color_map[relation["type"]],
            ec=color_map[relation["type"]],
            width=3,
        )
    ax1.axis("off")

    legend_handles = []
    legend_labels = []
    for relation_type, color in color_map.items():
        legend_handles.append(
            plt.Line2D(
                [0], [0], color=color, marker="o", linestyle="", label=relation_type
            )
        )
        legend_labels.append(relation_type)

    # Add the legend to ax2
    ax2.legend(
        handles=legend_handles,
        labels=legend_labels,
        loc="upper center",
        ncol=len(legend_handles),
    )
    ax2.axis("off")
    plt.tight_layout()

    # plt.show()
    plt.savefig("output/order_annotation.png", dpi=200)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="path to the path", type=str)
    parser.add_argument("-i", "--page_index", help="page index", type=int)
    args = parser.parse_args()

    path = args.path
    page_index = args.page_index

    visualize_order_annotation_single_page(path, page_index)


if __name__ == "__main__":
    main()
