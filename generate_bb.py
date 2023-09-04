import os
from PIL import Image
from typing import Dict, List

from pdfminer.high_level import extract_pages


def generate_bb(filename: str) -> Dict[int, List]:
    elements = {}
    page_layouts = extract_pages(filename)
    for page_index, page_layout in enumerate(page_layouts):
        elements[page_index] = []
        for element in page_layout:
            elements[page_index].append(element)

    return elements


def show_bb(image: Image, elements: Dict[int, List]):
    pass


def main():
    filename = os.path.expanduser("~/icml2022/example_paper.pdf")
    elements = generate_bb(filename)
    print(elements[0])
    


if __name__ == '__main__':
    main()
