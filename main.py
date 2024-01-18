import argparse
import glob
import os
import shutil
from tqdm import tqdm


from vrdu import logger
from vrdu import utils
from vrdu import renderer
from vrdu import preprocess
from vrdu import annotation
from vrdu.config import config


log = logger.setup_app_level_logger(file_name="vrdu_debug.log")


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
    redundant_folders = glob.glob(f"{main_directory}/output/{config.folder_prefix}*")
    redundant_folders += [
        f"{main_directory}/output/paper_white",
        f"{main_directory}/output/paper_original",
    ]
    for folder in redundant_folders:
        shutil.rmtree(folder)


def parse_arguments() -> str:
    """
    Parses the command line arguments and returns the name of the tex file.

    Returns:
        str: The name of the tex file with full path.

    Raises:
        argparse.ArgumentError: If the required file name argument is not provided.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file_name",
        type=str,
        required=True,
        help="The name of the tex file will full path",
    )
    args = parser.parse_args()
    file_name = args.file_name

    return file_name


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
    file_name = parse_arguments()
    main_directory = os.path.dirname(file_name)
    log.info(f"[VRDU] file: {file_name}, start processing.")

    # remove output folder if it exists
    output_directory = os.path.join(main_directory, "output")
    if os.path.exists(output_directory):
        shutil.rmtree(output_directory)

    # make a copy of the original tex file
    original_tex = os.path.join(main_directory, "paper_original.tex")
    shutil.copyfile(file_name, original_tex)

    cwd = os.getcwd()

    try:
        # change the working directory to the main directory
        os.chdir(main_directory)
        log.info(f"[VRDU] file: {original_tex}, start pre processing.")
        preprocess.run(original_tex)

        # run rendering
        log.info(f"[VRDU] file: {original_tex}, start rendering.")
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
        vrdu_annotation = annotation.LayoutAnnotation(main_directory)
        vrdu_annotation.annotate()

        log.info(f"[VRDU] file: {original_tex}, successfully processed.")

    except Exception:
        log.exception(f"[VRDU] file: {original_tex}, failed.")

    finally:
        # remove redundant files
        remove_redundant_stuff(main_directory)

        # Change back to original dir
        os.chdir(cwd)


if __name__ == "__main__":
    main()
