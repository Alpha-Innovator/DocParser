import os
import subprocess

from pdf2image import pdf2image


def compile_latex(file):
    path_name = os.path.dirname(file)
    file_name = os.path.basename(file)
    script_path = os.path.expanduser("scripts/compile_latex.sh")
    subprocess.run(["bash", script_path, path_name, file_name], check=True)


def pdf2jpg(pdf: str, path: str) -> None:
    """
    Convert a PDF file into a series of JPEG images.

    Parameters:
        pdf (str): The path of the PDF file to be converted.
        path (str): The directory where the converted images will be saved.

    Returns:
        None
    """
    os.makedirs(path, exist_ok=True)
    images = pdf2image.convert_from_path(pdf, fmt="png")

    for page_index, image in enumerate(images):
        # TODO: make this more flexible
        image_name = str(page_index) + ".png"
        image.save(os.path.join(path, image_name))


def convert_pdf_figure_to_png_image(pdf_image: str, png_image: str):
    subprocess.run(["pdfcrop", pdf_image, pdf_image])
    # convert the pdf image into png
    images = pdf2image.convert_from_path(pdf_image)
    images[0].save(png_image)
