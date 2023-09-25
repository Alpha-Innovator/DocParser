import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import argparse

from rendering.utils import load_json


def visualize(image_path, page_reading_info):
    # Define the bounding boxes
    bounding_boxes = [
        {
            "x": item["bbox"][0],
            "y": item["bbox"][1],
            "width": item["bbox"][2] - item["bbox"][0],
            "height": item["bbox"][3] - item["bbox"][1],
            "text": item["source"],
        }
        for item in page_reading_info
    ]

    # Load the image
    image = plt.imread(image_path)
    fig, ax = plt.subplots()
    ax.imshow(image)

    # Draw bounding boxes
    for bbox in bounding_boxes:
        x, y, width, height, text = (
            bbox["x"],
            bbox["y"],
            bbox["width"],
            bbox["height"],
            bbox["text"],
        )
        rect = patches.Rectangle(
            (x, y), width, height, linewidth=1, edgecolor="r", facecolor="none"
        )
        ax.add_patch(rect)
        rect.set_label(text)
        ax.text(
            x + width / 2,
            y + height / 2,
            text,
            ha="center",
            va="center",
            color="r",
            fontsize=12,
        )

    # Show the plot
    plt.show()


def parse_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--directory", type=str, required=True, help="Path to the image"
    )
    parser.add_argument(
        "--base_name", type=str, required=True, help="Base name of the image"
    )
    parser.add_argument("--page_index", type=int, required=True, help="Page index")
    args = parser.parse_args()
    return args.directory, args.base_name, args.page_index


def load_data(directory, basename, page_index):
    image_file_name = f"{basename}_annotation_page_{page_index}.png"
    image_path = os.path.join(directory, image_file_name)

    if not os.path.exists(image_path):
        raise FileNotFoundError("Wrong image path or file name or page index!")

    reading_annotation = os.path.join(directory, "reading_annotation.json")
    reading_infos = load_json(reading_annotation)
    page_reading_info = reading_infos[str(page_index)]

    return image_path, page_reading_info


def main():
    directory, basename, page_index = parse_argument()

    image_path, page_reading_info = load_data(directory, basename, page_index)

    visualize(image_path, page_reading_info)


if __name__ == "__main__":
    main()
