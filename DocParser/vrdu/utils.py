import os
import subprocess
import json
from typing import Any, Dict, List, Union


from pdf2image import pdf2image
from pdf2image import generators

from vrdu.block import Block
from vrdu.config import config


def export_to_json(data: Union[Dict, List], file_path: str) -> None:
    """
    Write the contents of a dictionary or a list to a JSON file.

    Parameters:
        data (Union[Dict, List]): The dictionary to be written to the file.
        file_path (str): The path to the JSON file.
    """
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)


def load_json(file_path: str) -> Union[Dict, List]:
    """
    Load a JSON file into a dictionary or a list.

    Parameters:
        file_path (str): The path to the JSON file.

    Returns:
        Union[Dict, List]: The loaded JSON data as a dictionary or a list.
    """
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
    return data


def compile_latex(file: str) -> None:
    """
    Compile a LaTeX file using pdflatex and bibtex engines.

    Parameters:
        file (str): The path to the LaTeX file to be compiled.

    Returns:
        None
    """
    file_name = os.path.basename(file)
    base_name, _ = os.path.splitext(file_name)

    # First compilation with SyncTeX
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", file_name],
        timeout=1000,
        stdout=subprocess.DEVNULL,
    )

    # Compile BibTeX if .aux file exists
    if os.path.exists(base_name + ".aux"):
        subprocess.run(
            ["bibtex", base_name],
            timeout=1000,
            stdout=subprocess.DEVNULL,
        )

    # Second compilation to include bibliography
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", file_name],
        timeout=1000,
        stdout=subprocess.DEVNULL,
    )

    # Third compilation to finalize references and SyncTeX
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode",  file_name],
        timeout=1000,
        stdout=subprocess.DEVNULL,
    )

    # Additional compilation for specific file
    if file_name == "paper_colored.tex":
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-synctex=1", file_name],
            timeout=1000,
            stdout=subprocess.DEVNULL,
        )

def pdf2jpg(pdf_path: str, output_directory: str) -> None:
    """
    Convert a PDF file into a series of jpg images.

    Parameters:
        pdf_path (str): The path of the PDF file to be converted.
        output_directory (str): The directory where the converted images will be saved.
    Returns:
        None

    Reference:
        https://pypi.org/project/pdf2image/
    """
    os.makedirs(output_directory, exist_ok=True)
    # the output images has name of format: thread-000x-yz.png
    # where x is the thread index, yz is the index of pdf page start from 1
    pdf2image.convert_from_path(
        pdf_path,
        fmt="jpg",
        output_folder=output_directory,
        output_file=generators.counter_generator(prefix="thread-", suffix="-page"),
    )


def convert_pdf_figure_to_png_image(pdf_image: str, png_image: str, dpi: int = 72):
    """
    Convert a PDF to a PNG image.

    Parameters:
        pdf_image (str): The filepath of the PDF image to convert.
        png_image (str): The filepath where the PNG image will be saved.
        dpi (int): The resolution for the conversion (default is 72).

    Returns:
        None
    """
    # crop the pdf image
    subprocess.run(
        ["pdfcrop", pdf_image, pdf_image],
        stdout=subprocess.DEVNULL,
    )
    # convert the pdf image into png
    images = pdf2image.convert_from_path(pdf_image, dpi=dpi)
    images[0].save(png_image)


def convert_eps_image_to_pdf_image(eps_image_path: str, pdf_image_path: str):
    """
    A function that converts an EPS image to a PDF image.

    Args:
        eps_image_path (str): The file path of the EPS image to convert.
        pdf_image_path (str): The file path where the PDF image will be saved.
    """
    subprocess.run(["epspdf", eps_image_path, pdf_image_path])


def export_to_coco(
    layout_info: Dict[int, List[Block]],
    image_infos: Dict[int, Dict[str, Any]],
    file_path: str,
) -> None:
    """
    Export the given layout information and image information to a COCO format JSON file.

    Args:
        layout_info (Dict[int, List[Block]]):
            A dictionary mapping page indices to lists of Block objects.
        image_infos (Dict[int, Dict[str, Any]]):
            A dictionary mapping page indices to dictionaries containing image information.
        file_path (str): The name of the output JSON file.

    Returns:
        None

    Reference:
        https://cocodataset.org/#format-data
    """
    category_info = [
        {
            "id": index,
            "name": category,
            "supercategory": supercategory,
        }
        for index, category, supercategory in config.config["category_name"]
    ]
    result = {
        "info": config.config["coco_info"],
        "licenses": config.config["coco_licenses"],
        "images": [],
        "annotations": [],
        "categories": category_info,
    }

    result["images"] = [
        {
            "id": page_index,
            "width": image_infos[page_index]["width"],
            "height": image_infos[page_index]["height"],
            "file_name": image_infos[page_index]["file_name"],
            **config.config["coco_image_info"],
        }
        for page_index in layout_info.keys()
    ]

    for page_index, page_elements in layout_info.items():
        for index, element in enumerate(page_elements):
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

    export_to_json(result, file_path)


def colorize(text: str, category_name: str) -> str:
    """
    Given a piece of text and a category name, colorizes the text based on the category.

    Args:
        text (str): The text to be colorized.
        category_name (str): The category name to determine the colorization.

    Returns:
        str: The colorized text based on the category.
    """
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
        return "{" + text[:prefix] + "\\color{" + color + "}" + text[prefix:] + "}"
    if category_name == "Code":
        return "{\\color{" + color + "}" + text + "}"


    raise NotImplementedError(f"Invalid category name: {category_name}")
