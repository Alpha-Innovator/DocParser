import datetime
import os
import re
import subprocess
import json
from typing import Any, Dict

from TexSoup.TexSoup import TexSoup
import TexSoup.app.conversion as conversion
from pdf2image import pdf2image

from vrdu.config import config


def export_to_json(data, file_path) -> None:
    """
    Write the contents of a dictionary to a JSON file.

    Parameters:
        data (dict): The dictionary to be written to the file.
        file_path (str): The path to the JSON file.
    """
    with open(file_path, "w") as json_file:
        json.dump(data, json_file)


def load_json(file_path) -> Any:
    """
    Load a JSON file into a dictionary.

    Parameters:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data as a dictionary.
    """
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
    return data


def get_main_content(data):
    """
    Generate the main content of a document.

    Parameters:
    - data (list): A list of dictionaries representing the document.

    Returns:
    - main_content (str): The main content of the document.

    Raises:
    - Exception: If the document is not found in the data.

    """
    main_content = None
    main_content_index = None
    for index, item in enumerate(data):
        if isinstance(item, dict) and "document" in item:
            main_content = item["document"][1]
            main_content_index = index
            break

    if main_content is None:
        raise Exception("document not found")

    return main_content, main_content_index


def extract_main_content(latex_file):
    """Extract content between \\begin{document} and \\end{document}"""

    with open(latex_file) as f:
        content = f.read()

    start = content.find("\\begin{document}")
    end = content.find("\\end{document}")

    if start == -1 or end == -1:
        raise ValueError("Document tags not found")

    start += len("\\begin{document}")
    main_content = content[start:end]

    return main_content, start, end


def data_from_tex_file(tex_file):
    """
    Reads a given tex file and extracts data from it.

    Args:
        tex_file (str): The path to the tex file.
        debug_mode (bool, optional): If True, enables debug mode. Defaults to False.

    Returns:
        list: The extracted data from the tex file.
    """
    main_content, start, end = extract_main_content(tex_file)
    tex_tree = TexSoup(main_content).expr.all
    data = conversion.to_list(tex_tree)

    return data, start, end


def tex_file_from_data(
    data: list, tex_file: str, start: int = 0, end: int = -1
) -> None:
    """
    Generate a TeX file from a dictionary/list of data.

    Args:
        data (list): The data to be converted into a TeX file.
        tex_file (str): The path to the output TeX file.
        debug_mode (bool, optional): Whether to enable debug mode. Defaults to False.
        start (int, optional): The start index. Defaults to 0.
        end (int, optional): The end index. Defaults to -1

    Returns:
        None: This function does not return anything.
    """

    # convert the data into latex
    rendered_tex = conversion.to_latex(data)

    with open(tex_file, "r") as f:
        content = f.read()

    content = content[:start] + rendered_tex + content[end:]

    with open(tex_file, "w") as f:
        f.write(content)


def replace_nth(string: str, old: str, new: str, n: int) -> str:
    """
    Replace the n-th occurrence of a substring in a given string with a new substring.

    Args:
        string (str): The original string to search and perform the replacement on.
        old (str): The substring to be replaced.
        new (str): The substring to replace the n-th occurrence of `old` in `string`.
        n (int): The occurrence number of `old` to be replaced (1-based index).

    Returns:
        str: The modified string with the n-th occurrence of `old` replaced by `new`. If the
             occurrence is not found, the original string is returned.

    Example:
        >>> replace_nth("Hello, hello, hello!", 'hello', 'hi', 2)
        'Hello, hello, hi!'
    """
    index_of_occurrence = string.find(old)
    occurrence = int(index_of_occurrence != -1)

    while index_of_occurrence != -1 and occurrence != n:
        index_of_occurrence = string.find(old, index_of_occurrence + 1)
        occurrence += 1

    if occurrence == n:
        return (
            string[:index_of_occurrence]
            + new
            + string[index_of_occurrence + len(old) :]
        )

    return string


def compile_latex(file):
    path_name = os.path.dirname(file)
    file_name = os.path.basename(file)
    script_path = os.path.expanduser("compile_latex.sh")
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
    subprocess.run(
        ["pdfcrop", pdf_image, pdf_image],
        stdout=subprocess.DEVNULL,
    )
    # convert the pdf image into png
    images = pdf2image.convert_from_path(pdf_image, dpi=72)
    images[0].save(png_image)


def export_to_coco(
    layout_info: Dict,
    image_infos: Dict[int, str],
    filename: str,
) -> None:
    category_info = [
        {"id": index, "name": category, "supercategory": supercategory}
        for index, category, supercategory in config.config["category_name"]
    ]
    result = {
        "info": config.config["coco_info"],
        "licenses": config.config["coco_licenses"],
        "images": [],
        "annotations": [],
        "categories": category_info,
    }

    for page_index, page_elements in layout_info.items():
        page_layout = page_elements[0]
        image = {
            "id": page_index,
            "width": page_layout.width,
            "height": page_layout.height,
            "file_name": image_infos[page_index],
        }
        image.update(config.config["coco_images"])
        result["images"].append(image)

        for index, element in enumerate(page_elements[1:]):
            width, height = element.width, element.height
            annotation = {
                "id": index,
                "image_id": page_index,
                "category_id": element.category,
                "segmentation": [],
                "bbox": [element.bbox[0], element.bbox[1], width, height],
                "area": width * height,
                "iscrowd": 0,
            }
            result["annotations"].append(annotation)

    with open(filename, "w") as f:
        json.dump(result, f)


def get_graphicspath(latex):
    graphicspath_re = r"\\graphicspath\{\{(.+?)}"

    match = re.search(graphicspath_re, latex, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return ""


def colorize(text: str, category_name: str) -> str:
    color = config.name2color[category_name]
    if category_name == "Caption":
        index = text.find("{")
        return text[: index + 1] + "{\\color{" + color + "}" + text[index + 1 :] + "}"
    if category_name == "Footnote":
        index = text.find("{")
        return text[: index + 1] + "\\color{" + color + "}" + text[index + 1 :]
    if category_name == "Table":
        return "{\\color{" + color + "}" + text + "}"
    if category_name == "Algorithm":
        # skip the position arguments, like \\begin{algorithm}[hbt!]
        index = text.find("\\", len("\\begin{algorithm}"))
        return text[:index] + "\\color{" + color + "}" + text[index:]
    if category_name == "Title":
        return r"{\color{" + color + "}" + text + "}"
    if category_name == "List":
        return r"{\color{" + color + "}" + text + "}"
    if category_name == "Text":
        return "\\textcolor{" + color + "}{" + text + "}"
    if category_name == "Text-EQ":
        return r"\textcolor{" + color + "}{" + text + "}"
    if category_name == "PaperTitle":
        index = text.find("{")
        return (
            text[: index + 1] + "\\textcolor{" + color + "}{" + text[index + 1 :] + "}"
        )
    if category_name == "Abstract":
        index = len("\\begin{abstract}")
    if category_name == "Code":
        return "{\\color{" + color + "}" + text + "}"

    raise NotImplementedError(f"Invalid category name: {category_name}")
