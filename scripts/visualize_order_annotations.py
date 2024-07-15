import argparse
from collections import defaultdict
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw
from matplotlib import pyplot as plt

from vrdu import utils


def draw_arrow_line(
    image: Image.Image,
    point_A: Tuple[float, float],
    point_B: Tuple[float, float],
    width: int = 1,
    color: Tuple[int, int, int] = (0, 255, 0),
) -> Image.Image:
    """
    Draws an arrow line between two points on an image.

    Args:
    image (PIL.Image.Image): The image on which to draw the arrow line.
    point_A (Tuple[float, float]): The first point of the arrow line.
    point_B (Tuple[float, float]): The second point of the arrow line.
    width (int, optional): The width of the arrow line. Defaults to 1.
    color (Tuple[int, int, int], optional): The color of the arrow line. Defaults to (0, 255, 0).

    Returns:
    PIL.Image.Image: The image with the arrow line drawn.

    """
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


def extract_relations(
    page_index: int, order_annotation_data: Dict[str, Any], width=None
) -> List[Tuple[Tuple[float, float], Tuple[float, float], str]]:
    """
    Extracts relations between blocks on a given page or across two adjacent pages.

    Args:
    page_index (int): The index of the page to extract relations for.
    order_annotation_data (Dict[str, Any]): The JSON file containing the order annotation data.
    width (int, optional): The width of the image. If not provided, it assumes a single page.

    Returns:
    List[Tuple[Tuple[float, float], Tuple[float, float], str]]: A list of tuples containing the coordinates of the block centers and the relation type.

    Raises:
    FileNotFoundError: If the order annotation JSON file or any of the image files are not found.

    Usage:
    ```python
    relations = extract_relations(10, order_annotation_data, 1000)
    ```
    """
    page_blocks = defaultdict(list)
    id2blocks = {}
    page2id2 = defaultdict(list)
    for block in order_annotation_data["annotations"]:
        page_blocks[block["page_index"]].append(block)
        id2blocks[block["block_id"]] = block
        page2id2[block["page_index"]].append(block["block_id"])

    # single page
    if width is None:
        relation_tuples = []
        for relation in order_annotation_data["orders"]:
            if relation["from"] not in page2id2[page_index]:
                continue
            if relation["to"] not in page2id2[page_index]:
                continue
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
            relation_tuples.append((center_from, center_to, relation["type"]))

        return relation_tuples

    # two page
    relation_tuples = []
    for relation in order_annotation_data["orders"]:
        if relation["from"] not in page2id2[page_index] + page2id2[page_index + 1]:
            continue
        if relation["to"] not in page2id2[page_index] + page2id2[page_index + 1]:
            continue
        block_from = id2blocks[relation["from"]]
        block_to = id2blocks[relation["to"]]

        center_x = (block_from["bbox"][0] + block_from["bbox"][2]) / 2
        center_y = (block_from["bbox"][1] + block_from["bbox"][3]) / 2
        if block_from["page_index"] != page_index:
            center_x += width
        center_from = (center_x, center_y)

        center_x = (block_to["bbox"][0] + block_to["bbox"][2]) / 2
        center_y = (block_to["bbox"][1] + block_to["bbox"][3]) / 2
        if block_to["page_index"] != page_index:
            center_x += width
        center_to = (center_x, center_y)

        relation_tuples.append((center_from, center_to, relation["type"]))
    return relation_tuples


def visualize_order_annotation_on_image(
    relation_tuples: List[Tuple[Tuple[float, float], Tuple[float, float], str]],
    image: Image.Image,
) -> None:
    """
    Visualizes the order annotation on an image.

    Args:
    relation_tuples (List[Tuple[Tuple[float, float], Tuple[float, float], str]]):
    A list of tuples containing the coordinates of the block centers and the relation type.
    image (PIL.Image.Image): The image on which to draw the arrow lines.

    Returns:
    None

    Raises:
    FileNotFoundError: If the order annotation JSON file or any of the image files are not found.

    Usage:
    ```python
    relation_tuples = extract_relations(10, order_annotation_data, 1000)
    visualize_order_annotation_on_image(relation_tuples, image)
    ```

    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(17, 22))
    ax1.imshow(image)
    color_map = {
        "identical": "green",
        "adj": "blue",
        "peer": "red",
        "implicit-cite": "purple",
        "explicit-cite": "brown",
        "sub": "orange",
    }

    for relation in relation_tuples:
        center_from, center_to, relation_type = relation
        ax1.arrow(
            center_from[0],
            center_from[1],
            center_to[0] - center_from[0],
            center_to[1] - center_from[1],
            fc=color_map[relation_type],
            ec=color_map[relation_type],
            width=3,
        )
    ax1.axis("off")

    legend_handles = []
    legend_labels = []
    relation_type_maps = {
        "identical": "identical",
        "adj": "non-title adjac",
        "peer": "title adjacent",
        "implicit-cite": "implicitly-referred",
        "explicit-cite": "explicitly-referred",
        "sub": "subordinate",
    }
    for relation_type, color in color_map.items():
        legend_handles.append(
            plt.Line2D(
                [0], [0], color=color, marker="o", linestyle="", label=relation_type
            )
        )
        legend_labels.append(relation_type_maps[relation_type])

    # Add the legend to ax2
    ax2.legend(
        handles=legend_handles,
        labels=legend_labels,
        loc="upper center",
        ncol=len(legend_handles),
    )
    ax2.axis("off")
    plt.tight_layout()

    plt.savefig(f"output/order_annotation.png", dpi=200)


def visualize_order_annotation_across_pages(path: Path, page_index: int) -> None:
    """
    Visualizes the order annotation across two adjacent pages.

    Args:
    path (Path): The path to the directory containing the images and the order annotation JSON file.
    page_index (int): The index of the first page to be visualized.

    Returns:
    None

    Raises:
    FileNotFoundError: If the order annotation JSON file or any of the image files are not found.

    Usage:
    ```python
    visualize_order_annotation_across_pages("/path/to/directory", 10)
    ```
    """
    order_annotation_file = os.path.join(path, "order_annotation.json")
    image_file1 = os.path.join(path, f"page_{page_index:04}.jpg")
    image_file2 = os.path.join(path, f"page_{page_index+1:04}.jpg")

    # extract blocks in this page
    order_annotation_data = utils.load_json(order_annotation_file)

    # visualize
    image1 = Image.open(image_file1)
    image2 = Image.open(image_file2)

    relation_tuples = extract_relations(page_index, order_annotation_data, image1.width)

    # concatenate adjacent pages
    width = image1.width + image2.width
    image = Image.new("RGB", (width, image1.height))
    image.paste(image1, (0, 0))
    image.paste(image2, (image1.width, 0))
    image.save(f"concatenated_image.png")

    visualize_order_annotation_on_image(relation_tuples, image)


def visualize_order_annotation_single_page(path: Path, page_index: int) -> None:
    """
    Visualizes the order annotation on a single page.

    Args:
    path (Path): The path to the directory containing the image and the order annotation JSON file.
    page_index (int): The index of the page to be visualized.

    Returns:
    None

    Raises:
    FileNotFoundError: If the order annotation JSON file or any of the image files are not found.

    Usage:
    ```python
    visualize_order_annotation_single_page("/path/to/directory", 10)
    ```
    """
    order_annotation_file = os.path.join(path, "order_annotation.json")
    order_annotation_data = utils.load_json(order_annotation_file)

    image_file = os.path.join(path, f"page_{page_index:04}.jpg")
    image = Image.open(image_file)

    # extract blocks in this page
    relation_tuples = extract_relations(page_index, order_annotation_data)

    # visualize
    visualize_order_annotation_on_image(relation_tuples, image)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="path to the path", type=str)
    parser.add_argument("-i", "--page_index", help="page index", type=int)
    args = parser.parse_args()

    path = args.path
    page_index = args.page_index

    visualize_order_annotation_single_page(path, page_index)
    # visualize_order_annotation_across_pages(path, page_index)


if __name__ == "__main__":
    main()
