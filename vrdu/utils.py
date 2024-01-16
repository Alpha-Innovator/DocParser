import csv
import glob
import os
import re
import subprocess
import json
from typing import Any, Dict, List
import uuid


from pdf2image import pdf2image
from pdf2image import generators

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


def compile_check(source_code: str) -> bool:
    """
    check if the source code can be compiled,
    used to check if there are macros in the source code.
    """
    prefix = r"""
    \documentclass{article}
    \usepackage{amsmath}
    \usepackage{amssymb}
    \usepackage{amsfonts, bm}
    \usepackage{amsthm}
    \usepackage{array}
    \usepackage{tabularx}
    \usepackage{multirow}
    \usepackage{booktabs}
    \begin{document}
    """

    suffix = r"""
    \end{document}
    """
    temp_filename = str(uuid.uuid4())
    content = prefix + source_code + suffix
    with open(f"{temp_filename}.tex", "w") as f:
        f.write(content)

    result = True
    try:
        subprocess.run(
            ["pdflatex", "-halt-on-error", f"{temp_filename}.tex"], check=True
        )
    except subprocess.CalledProcessError:
        result = False
    finally:
        # remove files
        files = glob.glob(f"{os.getcwd()}/{temp_filename}.*")
        for file in files:
            os.remove(file)

    return result


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





def compile_latex(file: str, tex_engine: str = "pdflatex"):
    path_name = os.path.dirname(file)
    file_name = os.path.basename(file)
    if tex_engine == "pdflatex":
        script_path = os.path.expanduser("compile_latex.sh")
        subprocess.run(["bash", script_path, path_name, file_name], check=True)
    elif tex_engine == "xelatex":
        subprocess.run(["xelatex", file], check=True)


def pdf2jpg(pdf: str, path: str) -> None:
    """
    Convert a PDF file into a series of jpg images.

    Parameters:
        pdf (str): The path of the PDF file to be converted.
        path (str): The directory where the converted images will be saved.
    Returns:
        None

    Reference:
        https://pypi.org/project/pdf2image/
    """
    os.makedirs(path, exist_ok=True)
    # the output images has name of format: thread-000x-yz.png
    # where x is the thread index, yz is the index of pdf page start from 1
    pdf2image.convert_from_path(
        pdf,
        fmt="jpg",
        output_folder=path,
        output_file=generators.counter_generator(prefix="thread-", suffix="-page"),
    )


def convert_pdf_figure_to_png_image(pdf_image: str, png_image: str, dpi: int = 72):
    # crop the pdf image
    subprocess.run(
        ["pdfcrop", pdf_image, pdf_image],
        stdout=subprocess.DEVNULL,
    )
    # convert the pdf image into png
    images = pdf2image.convert_from_path(pdf_image, dpi=dpi)
    images[0].save(png_image)


def convert_eps_image_to_pdf_image(eps_image_path: str, pdf_image_path: str):
    subprocess.run(["epspdf", eps_image_path, pdf_image_path])


def get_all_categories():
    """
    Retrieves all categories from the "category_count.csv" file.

    Returns:
        categories (list): A list of all categories.

    Reference:
        https://arxiv.org/category_taxonomy
    """
    categories = []
    with open("scripts/category_count.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            categories.append(row["categories"])

    return categories


def extract_tex_files(path) -> List[str]:
    """
    Given a path, this function extracts all the MAIN .tex files within the
    specified directory and its subdirectories.

    Args:
        path (str): The path to the directory where the .tex files are located.

    Returns:
        List[str]: A list of paths to the .tex files found.
    """
    tex_files = []

    for root, dirs, files in os.walk(path):
        for file in files:
            # skip non-tex files
            if not file.endswith(".tex"):
                continue
            # skip paper_*.tex files
            if file.startswith("paper_"):
                continue
            tex_file = os.path.join(root, file)

            try:
                with open(tex_file, "r") as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue

            # skip if this tex is not the main document
            if "\\begin{document}" not in content:
                continue

            tex_files.append(tex_file)
    return tex_files


def extract_macro_definitions(tex_file) -> List[str]:
    """
    Extracts macro definitions from a given tex file.

    Args:
        tex_file (str): The path to the tex file.

    Returns:
        List[str]: A list of macro definitions extracted from the tex file.
    """
    macro_patterns = [
        r"\\newcommand{[^}]+}",
        r"\\renewcommand{[^}]+}",
        r"\\newenvironment{[^}]+}",
        r"\\renewenvironment{[^}]+}",
    ]

    macros = []
    with open(tex_file, "r") as file:
        text_lines = file.readlines()
        macros = [
            line.strip()
            for line in text_lines
            if any(re.findall(pattern, line) for pattern in macro_patterns)
        ]

    return macros


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
        image.update(config.config["coco_image_info"])
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


def extract_title_name(title) -> str:
    """
    Extracts the name of a title from its format.

    Args:
        title (str): The title string to extract the name from.

    Returns:
        str: The extracted title environment name from the title.

    Example:
        >>> extract_title_name("\\section{Name}")
        'section'
        >>> extract_title_name("\\subsection*{AnotherName}")
        'subsection'
        >>> extract_title_name("No match")
        ''
    """
    match = re.search(r"\\(\w+)(\*?){(.*)}", title)
    if match:
        return match.group(1)

    return ""


def colorize(text: str, category_name: str) -> str:
    color = config.name2color[category_name]
    if category_name == "Caption":
        index = text.find("{")
        return text[: index + 1] + "{\\color{" + color + "}" + text[index + 1 :] + "}"
    if category_name == "Footnote":
        index = text.find("{")
        return text[: index + 1] + "{\\color{" + color + "}" + text[index + 1 :] + "}"
    if category_name == "Table":
        return "{\\color{" + color + "}" + text + "}"
    if category_name == "Algorithm":
        # skip the position arguments, like \\begin{algorithm}[hbt!]
        prefix = text.find("\\", len("\\begin{algorithm}"))
        suffix = text.find("\\end{algorithm}")
        return (
            text[:prefix]
            + "{\\color{"
            + color
            + "}"
            + text[prefix:suffix]
            + "}"
            + text[suffix:]
        )
    if category_name == "Title":
        return "{\\color{" + color + "}" + text + "}"
    if category_name == "List":
        return "{\\color{" + color + "}" + text + "}"
    if category_name == "Text":
        return "{\\textcolor{" + color + "}{" + text + "}}"
    if category_name == "Text-EQ":
        return "{\\textcolor{" + color + "}{" + text + "}}"
    if category_name == "PaperTitle":
        index = text.find("{")
        return (
            text[: index + 1]
            + "{\\textcolor{"
            + color
            + "}{"
            + text[index + 1 :]
            + "}}"
        )
    if category_name == "Equation":
        return "{\\color{" + color + "}{" + text + "}}"
    if category_name == "Abstract":
        prefix = len("\\begin{abstract}")
        suffix = len("\\end{abstract}")
        return (
            text[:prefix]
            + "{\\color{"
            + color
            + "}"
            + text[prefix:-suffix]
            + "}"
            + text[-suffix:]
        )
    if category_name == "Code":
        return "{\\color{" + color + "}" + text + "}"

    raise NotImplementedError(f"Invalid category name: {category_name}")
