import argparse

from preprocess.crop_pdf_image import crop_pdf_image
from preprocess.reduce_empty_lines import reduce_empty_lines
from preprocess.remove_comment_line import remove_comment_line
from preprocess.resolve_inputs import resolve_latex_imports
from preprocess.comment_lines import comment_sections


def run(tex_file):
    resolve_latex_imports(tex_file)
    comment_sections(tex_file)
    remove_comment_line(tex_file)
    reduce_empty_lines(tex_file)
    crop_pdf_image(tex_file)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tex_file", type=str, required=True, help="Path to the input tex file"
    )
    args = parser.parse_args()
    tex_file = args.tex_file
    return tex_file


def main():
    tex_file = parse_arguments()
    run(tex_file)


if __name__ == "__main__":
    main()
