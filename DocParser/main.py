import argparse
import glob
import os
import shutil
from pathlib import Path
from typing import List
from tqdm import tqdm
from loguru import logger

from DocParser.vrdu import utils
from DocParser.vrdu import renderer
from DocParser.vrdu import preprocess
from DocParser.vrdu import layout_annotation as layout
from DocParser.vrdu import order_annotation as order
from DocParser.vrdu.config import config
from DocParser.vrdu.quality_check import generate_quality_report

logger.add("vrdu_debug.log", mode="w")


def transform_tex_to_images(main_directory: Path) -> None:
    """
    Transforms TeX files with pattern paper_*.tex in the specified directory into jpg images.

    Args:
        main_directory (Path): The main directory where the TeX files are located.

    Returns:
        None
    """
    tex_files = glob.glob(f"{main_directory}/paper_*.tex")
    output_directory = Path(main_directory) / "output"
    for tex_file in tqdm(tex_files, desc="Converting TeX files to images"):
        logger.debug(f"[VRDU] file: {tex_file}, start transforming into images.")
        # Set colored flag based on filename
        colored = "paper_colored.tex" in tex_file
        utils.compile_latex(tex_file, colored=colored)

        # get the pdf file name
        filename_without_extension = Path(tex_file).stem
        pdf_file = Path(main_directory) / f"{filename_without_extension}.pdf"

        # convert into images
        image_directory = output_directory / filename_without_extension
        image_directory.mkdir(parents=True, exist_ok=True)
        utils.pdf2jpg(str(pdf_file), str(image_directory))


def get_redundant_folders(main_directory: Path) -> List[str]:
    """Get list of redundant folders to remove."""
    pattern = f"{main_directory}/output/paper_{config.folder_prefix}*"
    redundant_folders = glob.glob(pattern)
    redundant_folders.extend(
        [
            f"{main_directory}/output/paper_white",
            f"{main_directory}/output/paper_original",
        ]
    )
    return redundant_folders


def remove_redundant_stuff(main_directory: Path) -> None:
    """
    Remove redundant files and folders from the main directory.

    Args:
        main_directory (Path): The path of the main directory.

    Returns:
        None
    """
    # remove generated tex related files
    for file in glob.glob(f"{main_directory}/paper_*"):
        os.remove(file)

    # remove useless pdf and image files
    for folder in get_redundant_folders(main_directory):
        if os.path.exists(folder):
            shutil.rmtree(folder)


def check_if_already_processed(main_directory: Path) -> bool:
    quality_report_file = main_directory / "output/result/quality_report.json"
    return quality_report_file.exists()


def process_one_file(file_name: Path) -> None:
    """
    Process a file through multiple steps including preprocessing, rendering,
    transforming into images, generating annotations, and handling exceptions.

    Args:
        file_name (str): The path to the main .tex file to be processed.

    Returns:
        None
    """
    main_directory = Path(file_name).parent
    logger.info(f"[VRDU] file: {file_name}, start processing.")

    # check if this paper has been processed
    if check_if_already_processed(main_directory):
        logger.info(f"[VRDU] file: {file_name}, paper has been processed")
        return

    # make a copy of the original tex file
    original_tex = main_directory / "paper_original.tex"
    shutil.copyfile(file_name, original_tex)

    # remove the output folder if it exists
    output_directory = main_directory / "output"
    if output_directory.exists():
        shutil.rmtree(output_directory)

    # change the working directory to the main directory of the paper
    cwd = os.getcwd()

    try:
        # change the working directory to the main directory of the paper
        os.chdir(main_directory)
        # create output folder and output/result folder
        result_dir = output_directory / "result"
        result_dir.mkdir(parents=True)

        # step 1: preprocess the paper
        preprocess.run(original_tex)

        # step 2.1: run rendering
        vrdu_renderer = renderer.Renderer()
        vrdu_renderer.render(original_tex)

        # step 2.2: compiling tex into PDFs
        logger.info(
            f"[VRDU] file: {original_tex}, start transforming into images, this may take a while..."
        )
        transform_tex_to_images(main_directory)

        # Step 3: generate annotations
        logger.info(
            f"[VRDU] file: {original_tex}, start generating annotations, this may take a while..."
        )
        vrdu_layout_annotation = layout.LayoutAnnotation(original_tex)
        vrdu_layout_annotation.annotate()

        vrdu_order_annotation = order.OrderAnnotation(original_tex)
        vrdu_order_annotation.annotate()

        # generate quality report for simple debugging
        generate_quality_report(main_directory)

        logger.info(f"[VRDU] file: {original_tex}, successfully processed.")

    except Exception as e:
        # error_type = e.__class__.__name__
        # error_info = str(e)
        # logger.error(
        #     f"[VRDU] file: {file_name}, type: {error_type}, message: {error_info}"
        # )
        raise e

    finally:
        # remove redundant files
        remove_redundant_stuff(main_directory)

        # Change back to original dir
        os.chdir(cwd)


def main() -> None:
    """
    The main function that executes the entire program.

    This function takes no parameters and returns nothing.

    Steps:
    1. Parse command line arguments to get the file name.
    2. Get the main directory containing the file.
    3. Remove the output folder if it exists.
    4. Make a copy of the original tex file.
    5. Change the working directory to the main directory.
    6. Run the pre-processing step on the original tex file.
    7. Run the rendering step on the original tex file.
    8. Transform the tex file into images.
    9. Generate annotations for the tex file.
    10. Catch any exceptions during the processing and log the failure.
    11. Remove redundant files.
    12. Change back to the original directory.

    This function is the entry point of the program and orchestrates the entire processing pipeline.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Process TeX files to generate annotations and images"
    )
    parser.add_argument(
        "-f",
        "--file_name",
        type=Path,
        required=True,
        help="The path to the TeX file to process",
    )
    args = parser.parse_args()
    process_one_file(Path(args.file_name))


if __name__ == "__main__":
    main()
