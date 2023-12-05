import os
import re

from vrdu.config import envs
from vrdu import utils
from arxiv_cleaner.cleaner import Cleaner


def clean_tex(original_tex):
    input_dir = os.path.dirname(original_tex)
    tex = os.path.basename(original_tex)

    # Create the command options
    command_options = {
        "latex": {
            "compiler": "pdflatex",
            "extra_args": "",
        },
        "bib": {
            "compiler": "bibtex",
            "extra_args": "",
        },
        "latexpand": {
            "extra_args": "",
        },
    }

    # Create the cleaner
    cleaner = Cleaner(
        input_dir=input_dir,
        output_dir=input_dir,
        tex=tex,
        command_options=command_options,
        verbose=False,
    )

    # Run the cleaner
    cleaner.clean()


def replace_pdf_figures_with_png(tex_file):
    path = os.path.dirname(tex_file)
    with open(tex_file) as f:
        content = f.read()

    graphic_path = utils.get_graphicspath(content)

    # Regular expression pattern to match \includegraphics
    # commands with PDF files
    pattern = r"\\includegraphics(\[.*?\])?\{(.*?\.pdf)\}"

    # Find all matches of \includegraphics with PDF files
    matches = re.findall(pattern, content)

    # Replace PDF paths with PNG paths
    for match in matches:
        # crop the pdf image
        pdf_image_name = match[1]
        pdf_image = os.path.join(path, graphic_path + pdf_image_name)
        png_image_name = os.path.splitext(pdf_image_name)[0] + ".png"
        png_image = os.path.join(path, graphic_path + png_image_name)

        utils.convert_pdf_figure_to_png_image(pdf_image, png_image)

        # replace the reference in tex file
        content = content.replace(match[1], png_image_name)

    with open(tex_file, "w") as f:
        f.write(content)


def delete_table_of_contents(original_tex):
    with open(original_tex, "r") as file:
        latex_content = file.read()

    pattern = r"\\(" + "|".join(envs.table_of_contents) + r")"
    modified_content = re.sub(pattern, "", latex_content)

    with open(original_tex, "w") as file:
        file.write(modified_content)


def run(original_tex: str) -> None:
    path = os.path.dirname(original_tex)
    # Step 0: check if the file is compilable

    # Step 1: clean tex
    clean_tex(original_tex)

    # Step 2: process images
    replace_pdf_figures_with_png(original_tex)

    # Step 3: delete table of contents
    delete_table_of_contents(original_tex)

    # create output folder
    os.makedirs(os.path.join(path, "output/result"), exist_ok=True)
