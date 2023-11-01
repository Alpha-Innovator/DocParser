import argparse
import subprocess
import os
import re

from pdf2image.pdf2image import convert_from_path


def replace_pdf_with_png(tex_file):
    path = os.path.dirname(tex_file)
    with open(tex_file) as f:
        content = f.read()

    # Regular expression pattern to match \includegraphics
    # commands with PDF files
    pattern = r"\\includegraphics(\[.*?\])?\{(.*?\.pdf)\}"

    # Find all matches of \includegraphics with PDF files
    matches = re.findall(pattern, content)

    # Replace PDF paths with PNG paths
    for match in matches:
        # crop the pdf image
        pdf_image_name = match[1]
        pdf_image = os.path.join(path, pdf_image_name)
        subprocess.run(["pdfcrop", pdf_image, pdf_image])

        # convert the pdf image into png
        png_image_name = os.path.splitext(pdf_image_name)[0] + ".png"
        png_image = os.path.join(path, png_image_name)
        convert_pdf_to_png(pdf_image, png_image)

        # replace the reference in tex file
        content = content.replace(match[1], png_image_name)

    with open(tex_file, "w") as f:
        f.write(content)


def convert_pdf_to_png(pdf_image: str, png_image: str):
    images = convert_from_path(pdf_image)
    images[0].save(png_image)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_tex", type=str, required=True, help="Path to the input tex file"
    )
    args = parser.parse_args()
    tex_file = args.input_tex
    return tex_file


def main():
    tex_file = parse_arguments()
    replace_pdf_with_png(tex_file)


if __name__ == "__main__":
    main()
