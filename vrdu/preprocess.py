import os
import re

from arxiv_cleaner.cleaner import Cleaner

from vrdu.config import envs, config
from vrdu import utils
import vrdu.logger as logger


log = logger.get_logger(__name__)


def get_graphicspath(latex: str) -> str:
    """
    Returns the graphics path from a LaTeX string.

    Args:
        latex (str): The LaTeX string to search for the graphics path.

    Returns:
        str: The graphics path found in the LaTeX string, or an empty string if no graphics path is found.
    """
    graphicspath_re = r"\\graphicspath\{\{(.+?)}"

    match = re.search(graphicspath_re, latex, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return ""


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


def replace_pdf_ps_figures_with_png(original_tex: str) -> None:
    """
    Replaces PDF, ps, eps figures with PNG figures in a TeX file
    to support pdfminer detecting bounding box.

    Args:
        original_tex (str): The path to the original TeX file.

    Returns:
        None: This function does not return anything.

    Raises:
        FileNotFoundError: If a PDF file specified in the TeX file is not found.
    """
    main_directory = os.path.dirname(original_tex)
    with open(original_tex) as f:
        content = f.read()

    graphic_path = get_graphicspath(content)

    # Replace \psfig{...} with \includegraphics{...}
    content = re.sub(r'\\psfig{([^}]*)}', r'\\includegraphics{\1}', content)
    
    # Replace \epsfig{...} with \includegraphics{...}
    content = re.sub(r'\\epsfig{([^}]*)}', r'\\includegraphics{\1}', content)

    # Regular expression pattern to match \includegraphics
    # commands with PDF files
    pattern = r"\\includegraphics(\[.*?\])?\{(.*?\.pdf)\}"

    # Find all matches of \includegraphics with PDF files
    matches = re.findall(pattern, content)

    # Replace PDF paths with PNG paths
    for match in matches:
        image_name = match[1]
        image_file = os.path.join(main_directory, graphic_path, image_name)
        if not os.path.exists(image_file):
            raise FileNotFoundError(f"File not found: {image_file}")

        png_image_name = os.path.splitext(image_name)[0] + ".png"
        png_image = os.path.join(main_directory, graphic_path, png_image_name)

        utils.convert_pdf_figure_to_png_image(image_file, png_image)

        # replace the reference in tex file
        content = content.replace(match[1], png_image_name)

    with open(original_tex, "w") as f:
        f.write(content)


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

    # Step 2: process images
    replace_pdf_ps_figures_with_png(original_tex)

    # Step 3: delete table of contents
    delete_table_of_contents(original_tex)

    # create output folder
    main_directory = os.path.dirname(original_tex)
    os.makedirs(os.path.join(main_directory, "output/result"))
