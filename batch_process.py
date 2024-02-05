import os
import glob
import shutil
import argparse
import multiprocessing
from typing import List
from uuid import uuid4

from tqdm import tqdm

from vrdu import logger
from vrdu import utils
from vrdu import renderer
from vrdu import preprocess
from vrdu.annotation import LayoutAnnotation
from vrdu.config import config


log_file = str(uuid4()) + ".log"
log = logger.setup_app_level_logger(file_name=log_file, level="INFO", mode="a")


def transform_tex_to_images(main_directory: str) -> None:
    """
    Transforms TeX files with pattern paper_*.tex in the specified directory into jpg images.

    Args:
        main_directory (str): The main directory where the TeX files are located.

    Returns:
        None
    """
    tex_files = glob.glob(f"{main_directory}/paper_*.tex")
    output_directory = os.path.join(main_directory, "output")
    for tex_file in tqdm(tex_files):
        log.debug(f"[VRDU] file: {tex_file}, start transforming into images.")
        utils.compile_latex(tex_file)

        # get the pdf file name
        filename_without_extension = os.path.splitext(os.path.basename(tex_file))[0]
        pdf_file = os.path.join(main_directory, f"{filename_without_extension}.pdf")

        # convert into images
        image_directory = os.path.join(output_directory, filename_without_extension)
        os.makedirs(image_directory)
        utils.pdf2jpg(pdf_file, image_directory)


def remove_redundant_stuff(main_directory: str) -> None:
    """
    Remove redundant files and folders from the main directory.

    Args:
        main_directory (str): The path of the main directory.

    Returns:
        None
    """
    # remove generated tex related files
    redundant_files = glob.glob(f"{main_directory}/paper_*")
    for file in redundant_files:
        os.remove(file)

    # remove useless pdf and image files
    # TODO: move this name pattern into config
    redundant_folders = glob.glob(
        f"{main_directory}/output/paper_{config.folder_prefix}*"
    )
    redundant_folders += [
        f"{main_directory}/output/paper_white",
        f"{main_directory}/output/paper_original",
    ]
    for folder in redundant_folders:
        shutil.rmtree(folder)


def process_one_file(file_name) -> None:
    main_directory = os.path.dirname(file_name)
    log.info(f"[VRDU] file: {file_name}, start processing.")

    # check if this paper has been processed
    quality_report_file = os.path.join(
        main_directory, "output/result/quality_report.json"
    )
    if os.path.exists(quality_report_file):
        log.info(f"[VRDU] file: {file_name}, paper has been processed")
        return

    # make a copy of the original tex file
    original_tex = os.path.join(main_directory, "paper_original.tex")
    shutil.copyfile(file_name, original_tex)

    cwd = os.getcwd()

    try:
        # change the working directory to the main directory
        os.chdir(main_directory)
        preprocess.run(original_tex)

        # run rendering
        vrdu_renderer = renderer.Renderer()
        vrdu_renderer.render(original_tex)

        # compile into PDFs, and then convert into images
        log.info(
            f"[VRDU] file: {original_tex}, start transforming into images, this may take a while..."
        )
        transform_tex_to_images(main_directory)

        # generate annotations
        log.info(
            f"[VRDU] file: {original_tex}, start generating annotations, this may take a while..."
        )
        vrdu_annotation = LayoutAnnotation(main_directory)
        vrdu_annotation.annotate()

        log.info(f"[VRDU] file: {original_tex}, successfully processed.")

    except Exception as e:
        error_type = e.__class__.__name__
        error_info = str(e)
        log.error(
            f"[VRDU] file: {file_name}, type: {error_type}, message: {error_info}"
        )

    finally:
        # remove redundant files
        remove_redundant_stuff(main_directory)

        # Change back to original dir
        os.chdir(cwd)


def filter_tex_files(tex_files: List[str]) -> List[str]:
    """extract all MAIN.tex files for processing

    Args:
        tex_files (List[str]): list of tex files

    Returns:
        List[str]: list of tex files that are compiable.
    """
    result = []
    for tex_file in tex_files:
        # prevent processing previous generated files
        if os.path.basename(tex_file).startswith("paper_"):
            log.debug(f"{tex_file} should be deleted.")
            continue
        try:
            with open(tex_file) as f:
                content = f.read()
            if content.find(r"\\begin{document}") == -1:
                continue
            result.append(tex_file)
        except UnicodeDecodeError:
            log.debug(f"failed to read tex file: {tex_file}")
            continue

    return result


def process_one_category(path, cpu_count, category):
    category_path = os.path.join(path, category)
    log.info(f"path to raw data: {category_path}")
    log.info(f"Using cpu counts: {cpu_count}")
    tex_files = utils.extract_all_tex_files(category_path)
    tex_files = filter_tex_files(tex_files)
    log.info(f"Found {len(tex_files)} tex files")

    try:
        with multiprocessing.Pool(cpu_count) as pool:
            pool.map(process_one_file, tex_files)
        # save log file
    except Exception:
        log.exception(f"[VRDU] category: {category}, failed to process.")
    finally:
        # save the process log
        shutil.move(log_file, f"batch_process_{category}.log")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, required=True)
    parser.add_argument("-c", "--cpu_count", type=int, required=True)
    parser.add_argument("-t", "--category", type=str, required=False)
    args = parser.parse_args()
    path, cpu_count, category = args.path, args.cpu_count, args.category

    categories = [category] if category is not None else utils.get_all_categories()

    for category in categories:
        log.info(f"Processing single category: {category}")
        process_one_category(path, cpu_count, category)
