import os
import re

from arxiv_cleaner.cleaner import Cleaner

from vrdu.config import envs, config
from vrdu import utils
import vrdu.logger as logger


log = logger.get_logger(__name__)


def remove_comments(original_tex: str) -> None:
    """
    Removes comments from a TeX file.

    Args:
        original_tex (str): The path to the original TeX file.

    Returns:
        None
    """
    with open(original_tex, "r") as file:
        content = file.read()

    # Remove LaTeX comments
    pattern = r"\\begin{comment}(.*?)\\end{comment}"
    removed_comments = re.sub(pattern, "", content, flags=re.DOTALL)

    with open(original_tex, "w") as file:
        file.write(removed_comments)


def clean_tex(original_tex: str) -> None:
    """
    Clean the given TeX file by creating a cleaner object and running the clean method.

    Args:
        original_tex (str): The path to the original TeX file.

    Returns:
        None
    """
    main_directory = os.path.dirname(original_tex)
    tex = os.path.basename(original_tex)

    # Create the cleaner
    cleaner = Cleaner(
        input_dir=main_directory,
        output_dir=main_directory,
        tex=tex,
        command_options=config.command_options,
        verbose=False,
    )

    # Run the cleaner
    cleaner.clean()

    # remove comments
    remove_comments(original_tex)


def replace_figures_extension_with_png(original_tex: str) -> None:
    """
    Replaces PDF, ps, eps figures' extension with PNG in a TeX file
    to support pdfminer detecting bounding box.

    Args:
        original_tex (str): The path to the original TeX file.

    Returns:
        None: This function does not return anything.
    """
    main_directory = os.path.dirname(original_tex)
    image_extensions = [".eps", ".ps", ".jpg", ".jpeg", ".png", ".pdf"]
    image_files = {}
    for root, _, files in os.walk(main_directory):
        for file in files:
            if any(file.endswith(ext) for ext in image_extensions):
                image_name, ext = os.path.splitext(file)
                # Store the relative path of the image as the value
                image_files[image_name] = os.path.relpath(os.path.join(root, file), main_directory)

    with open(original_tex, 'r') as f:
        content = f.read()

    # Replace \psfig and \epsfig commands with \includegraphics command
    def custom_replace(match):
        options = match.group(1) or ''
        filepath = match.group(2)
        if options:
            return f"\\includegraphics[{options}]{{{filepath}}}"
        else:
            return f"\\includegraphics{{{filepath}}}"

    content = re.sub(r"\\psfig(?:\[(.*?)\])?{(.+?)}", custom_replace, content)
    content = re.sub(r"\\epsfig(?:\[(.*?)\])?{(.+?)}", custom_replace, content)

    # Traverse the image_files dictionary to update file extensions
    for image_name, file_path in image_files.items():
        base_name, current_extension = os.path.splitext(image_name)
        correct_extension = os.path.splitext(file_path)[1]

        if correct_extension not in ['.jpg', '.jpeg']:
            correct_extension = '.png'

        # Build a regular expression to match image files including optional extensions
        pattern = re.compile(r'(\\includegraphics(?:\[[^\]]*\])?\{.*?' + re.escape(base_name) + r')(\.\w+)?\}')
        replacement = rf'\1{correct_extension}}}'
        content = pattern.sub(replacement, content)

    # Write the updated content back to the file
    with open(original_tex, 'w') as f:
        f.write(content)


def replace_figures_in_folders(image_files: Dict[str, str]) -> None:
    for image_name, file_path in image_files.items():
        if file_path.endswith(".eps") or file_path.endswith(".ps"):
            output_png = os.path.join(os.path.dirname(file_path), image_name + ".png")
            temp_pdf = os.path.join(os.path.dirname(file_path), image_name + ".pdf")
            # convert eps to pdf
            utils.convert_eps_image_to_pdf_image(file_path, temp_pdf)
            # convert pdf to png
            utils.convert_pdf_figure_to_png_image(temp_pdf, output_png)
        elif file_path.endswith(".pdf"):
            output_png = os.path.join(os.path.dirname(file_path), image_name + ".png")
            # convert pdf to png
            utils.convert_pdf_figure_to_png_image(file_path, output_png)



def delete_table_of_contents(original_tex: str) -> None:
    """
    Deletes the table of contents from the given original_tex file.
    This includes table of contents, list of figures, list of tables, and list of algorithms.

    Parameters:
        original_tex (str): The path to the original .tex file.

    Returns:
        None
    """
    with open(original_tex, "r") as file:
        latex_content = file.read()

    pattern = r"\\(" + "|".join(envs.table_of_contents) + r")"
    modified_content = re.sub(pattern, "", latex_content)

    with open(original_tex, "w") as file:
        file.write(modified_content)


def run(original_tex: str) -> None:
    """
    Generates a modified version of the given LaTeX document by performing the following steps:

    Step 0: Clean the LaTeX document with arxiv_cleaner package.
    Step 1: Replace EPS figures with PDF to make the LaTeX document compilable with pdflatex.
    Step 2: Replace PDF figures with PNG to make pdfminer work.
    Step 3: Delete the table of contents from the LaTeX document.

    Args:
        original_tex (str): The original LaTeX document.

    Returns:
        None
    """
    # Step 0: clean tex
    clean_tex(original_tex)

    # Step 1: process images
    replace_figures_extension_with_png(original_tex)

    # Step 2: generate png figures
    generate_png_figure(original_tex)

    # Step 3: delete table of contents
    delete_table_of_contents(original_tex)
