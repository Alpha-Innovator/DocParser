from collections import defaultdict
import os
import matplotlib.pyplot as plt
import numpy as np
import csv


def get_all_categories():
    """
    Retrieves all categories from the "category_count.csv" file.

    Returns:
        categories (list): A list of all categories.

    Reference:
        https://arxiv.org/category_taxonomy
    """
    categories = []
    with open("scripts/category_count.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            categories.append(row["categories"])

    return categories


def visualize_distribution(dict1, dict2):
    categories = list(dict1.keys())  # Get the list of categories

    # Get the number of files for each category from both dictionaries
    files_dict1 = [dict1[category] for category in categories]
    files_dict2 = [dict2[category] for category in categories]

    # normalize
    files_dict1 = [x / sum(files_dict1) for x in files_dict1]
    files_dict2 = [x / sum(files_dict2) for x in files_dict2]

    # Set up the plot
    plt.figure(figsize=(10, 8))
    fig, ax = plt.subplots()
    width = 1.2  # Width of the bars

    # Calculate the positions for the bars
    positions = np.arange(0, len(categories) * width, width)

    # Plot the number of files for each category
    ax.barh(positions, files_dict1, width, label="batch", align="center", color="blue")
    ax.barh(
        positions,
        -np.array(files_dict2),
        width,
        label="original",
        align="center",
        color="red",
    )

    # Add labels and title to the plot
    ax.set_yticks(positions)
    ax.set_yticklabels(categories, fontsize=2)
    ax.set_xlabel("Number of Files")
    ax.set_title("Distribution of arxiv_source_uncompressed")
    ax.legend()

    plt.subplots_adjust(left=0.4)
    # Display the plot
    plt.savefig("test.png", dpi=300)


def analyze_raw_data(path):
    all_categories = get_all_categories()

    data = defaultdict(int)
    for category in all_categories:
        if os.path.exists(os.path.join(path, category)):
            data[category] = len(os.listdir(os.path.join(path, category)))

    with open("scripts/batch_count.csv", mode="w") as f:
        fieldnames = ["categories", "count"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key, value in data.items():
            writer.writerow(
                {
                    "categories": key,
                    "count": value,
                }
            )

    return data


def main():
    batch = analyze_raw_data(
        "/cpfs01/shared/ADLab/datasets/arxiv_source/arxiv_source_uncompressed"
    )

    original = {}
    with open("scripts/category_count.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            original[row["categories"]] = int(row["count"])

    visualize_distribution(batch, original)


if __name__ == "__main__":
    main()
