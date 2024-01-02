import matplotlib.pyplot as plt
import numpy as np
import csv


def visualize_distribution(dict1, dict2):
    categories = list(dict1.keys())  # Get the list of categories

    # Get the number of files for each category from both dictionaries
    files_dict1 = [dict1[category] for category in categories]
    files_dict2 = [dict2[category] for category in categories]

    # normalize
    files_dict1 = [x / sum(files_dict1) for x in files_dict1]
    files_dict2 = [x / sum(files_dict2) for x in files_dict2]

    # Set up the plot
    plt.figure(figsize=(800, 600))
    fig, ax = plt.subplots()
    width = 0.6  # Width of the bars

    # Calculate the positions for the bars
    positions = np.arange(len(categories))

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
    # ax.set_yticks(positions)
    # ax.set_yticklabels(categories)
    ax.set_xlabel("Number of Files")
    ax.set_title("Distribution of Number of Files")
    ax.legend()

    plt.subplots_adjust(left=0.4)
    # Display the plot
    # plt.show()
    plt.savefig("test.png")


batch = {}
with open("batch.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        batch[row["category"]] = int(row["number of files"])

original = {}
with open("scripts/category_count.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        original[row["categories"]] = int(row["count"])


visualize_distribution(batch, original)
