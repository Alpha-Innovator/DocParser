import glob
import shutil
import re
import os
import argparse
import pandas as pd
import multiprocessing

from vrdu import logger

log = logger.setup_app_level_logger(file_name="export_to_dataset.log")


json_files = [
    "layout_annotation.json",
    "order_annotation.json",
    "reading_annotation.json",
]


def export_one_paper(main_path: str, target_path: str) -> None:
    """
    Processes a single paper from the input directory and exports it to the target directory.

    Args:
    main_path (str): The path to the input directory containing the paper to be processed.
    target_path (str): The path to the target directory where the processed paper will be exported.

    Returns:
    None

    Raises:
    FileNotFoundError: If the target directory does not exist and cannot be created.

    Purpose:
    This function processes a single paper by copying its quality report, annotation files,
    and images to a new directory within the target directory.

    Steps:
    1. Logs the processing of the paper.
    2. Extracts the output directory and result directory from the input directory.
    3. Checks if the target directory for the discipline exists, if not, it creates it.
    4. Creates a new directory for the paper within the target directory.
    5. Copies the quality report file to the new directory.
    6. Copies the annotation files to the new directory.
    7. Copies the original images to the new directory,
       renaming them with a format of "original-page-{page_index}.jpg".
    8. Copies the annotated images to the new directory.
    """
    log.info(f"processing paper: {main_path}")
    output_path = os.path.join(main_path, "output")
    result_path = os.path.join(output_path, "result")

    paper_id = os.path.basename(main_path)
    discipline = os.path.basename(os.path.dirname(main_path))

    target_discipline_path = os.path.join(target_path, discipline)
    if not os.path.exists(target_discipline_path):
        os.makedirs(target_discipline_path)

    new_paper_path = os.path.join(target_discipline_path, paper_id)
    if os.path.exists(new_paper_path):
        return

    os.makedirs(new_paper_path)

    # coy quality report file
    quality_report_file = os.path.join(result_path, "quality_report.json")
    shutil.copy(quality_report_file, new_paper_path)

    # copy annotation files
    for json_file in json_files:
        shutil.copy(os.path.join(result_path, json_file), new_paper_path)

    # copy images
    original_image_path = os.path.join(output_path, "paper_colored")

    original_images = glob.glob(os.path.join(original_image_path, "*.jpg"))
    for image in original_images:
        filename = os.path.basename(image)
        match = re.search(r"page-(\d+)", filename)
        page_index = int(match.group(1)) - 1
        new_image_name = "original-page-{}.jpg".format(str(page_index).zfill(4))

        shutil.copy(image, os.path.join(new_paper_path, new_image_name))

    annotated_images = glob.glob(os.path.join(result_path, "*.jpg"))
    for image in annotated_images:
        shutil.copy(image, new_paper_path)
    os.makedirs(new_paper_path)

    # coy quality report file
    quality_report_file = os.path.join(result_path, "quality_report.json")
    shutil.copy(quality_report_file, new_paper_path)

    # copy annotation files
    for json_file in json_files:
        shutil.copy(os.path.join(result_path, json_file), new_paper_path)

    # copy images
    original_image_path = os.path.join(output_path, "paper_colored")

    original_images = glob.glob(os.path.join(original_image_path, "*.jpg"))
    for image in original_images:
        filename = os.path.basename(image)
        match = re.search(r"page-(\d+)", filename)
        page_index = int(match.group(1)) - 1
        new_image_name = "original-page-{}.jpg".format(str(page_index).zfill(4))

        shutil.copy(image, os.path.join(new_paper_path, new_image_name))

    annotated_images = glob.glob(os.path.join(result_path, "*.jpg"))
    for image in annotated_images:
        shutil.copy(image, new_paper_path)


def export_to_dataset(database_file: str, output_path: str) -> None:
    """
    Exports processed papers from the provided database file to the specified output path.

    Args:
    database_file (str): The path to the processed database file containing the list of processed papers.
    output_path (str): The path to the target directory where the processed papers will be exported.

    Returns:
    None

    Raises:
    FileNotFoundError: If the target directory does not exist and cannot be created.

    Purpose:
    This function exports the processed papers by processing each paper individually
    and exporting it to the target directory.

    Steps:
    1. Reads the processed database file and filters the papers with a status of "success".
    2. Logs the number of processed papers.
    3. Creates a list of arguments containing tuples of processed papers and the output path.
    4. Creates a multiprocessing pool with 28 processes.
    5. Uses the pool to starmap the export_one_paper function on the list of arguments.

    Note:
    The export_one_paper function is responsible for processing a single paper
    and exporting it to the target directory.
    """
    df = pd.read_csv(database_file)
    processed_papers = df[df["status"] == "success"]["path"].tolist()
    log.info(f"There are {len(processed_papers)} papers")

    arguments = [(paper, output_path) for paper in processed_papers]
    with multiprocessing.Pool(processes=28) as pool:
        pool.starmap(export_one_paper, arguments)


def main() -> None:
    """
    The main function that parses command-line arguments and calls the export_to_dataset function.

    Args:
    None

    Returns:
    None

    Raises:
    None

    Purpose:
    This function is the entry point of the script. It parses the command-line arguments
    using the argparse module and then calls the export_to_dataset function with the provided arguments.

    Steps:
    1. Create an ArgumentParser object to parse the command-line arguments.
    2. Add two command-line arguments: "-d" for the processed database file and "-o" for the output path of the dataset.
    3. Parse the command-line arguments using the parse_args() method of the ArgumentParser object.
    4. Call the export_to_dataset function with the parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--database_file", type=str, help="processed database file"
    )
    parser.add_argument("-o", "--output_path", type=str, help="output path of dataset")
    args = parser.parse_args()

    export_to_dataset(args.database_file, args.output_path)


if __name__ == "__main__":
    main()
