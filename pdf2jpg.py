import os
import argparse

from pdf2image.pdf2image import convert_from_path


def pdf2jpg(pdf: str, path: str) -> None:
    """
    Convert a PDF file into a series of JPEG images.

    Parameters:
        pdf (str): The path of the PDF file to be converted.
        path (str): The directory where the converted images will be saved.

    Returns:
        None
    """
    if not os.path.exists(path):
        os.makedirs(path)
    pdf_name = os.path.splitext(os.path.basename(pdf))[0]
    images = convert_from_path(pdf)
    for page_index, image in enumerate(images):
        image_name = pdf_name + '_page_' + str(page_index) + '.jpg'
        image.save(os.path.join(path, image_name), 'JPEG')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', type=str, required=True)
    parser.add_argument('--output_path', type=str, required=True)
    args = parser.parse_args()
    pdf2jpg(args.pdf, args.output_path)

if __name__ == '__main__':
    main()
