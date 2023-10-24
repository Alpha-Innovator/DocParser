import subprocess
import os
import re


def crop_pdf_image(tex_file: str) -> None:
    """Crop PDF images included in a LaTeX file.

    This function takes a LaTeX file (.tex) as input and crops any embedded
    PDF images that are included using includegraphics. It finds all instances
    of includegraphics and crops the referenced PDF files using the 'pdfcrop'
    command.

    The PDF files are cropped in-place, overwriting the original files.

    Arguments:
        tex_file (str): Path to the LaTeX file.

    Returns:
        None

    Reference:
        https://pdfcrop.sourceforge.net/
    """
    path = os.path.dirname(tex_file)
    with open(tex_file) as f:
        file_content = f.read()

    includegraphics_pattern = r"\\includegraphics\{(.*?)\}"
    for match_str in re.finditer(includegraphics_pattern, file_content):
        pdf_name = match_str.group(1)
        if not match_str.endswith(".pdf"):
            continue
        pdf_graphic = os.path.join(path, pdf_name)
        subprocess.run(["pdfcrop", pdf_graphic, pdf_graphic])
