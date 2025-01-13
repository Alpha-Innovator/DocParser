"""Utility functions for LaTeX document processing and file operations."""

import re
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pdf2image import pdf2image, generators
from DocParser.TexSoup.TexSoup import TexSoup
import DocParser.TexSoup.app.conversion as conversion
from DocParser.vrdu.block import Block
from DocParser.vrdu.config import config


def export_to_json(data: Union[Dict, List], file_path: Union[str, Path]) -> None:
    """Write data to a JSON file with indentation.

    Args:
        data: Dictionary or list to write
        file_path: Output JSON file path
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def load_json(file_path: Union[str, Path]) -> Union[Dict, List]:
    """Load data from a JSON file.

    Args:
        file_path: Input JSON file path

    Returns:
        Loaded dictionary or list
    """
    with open(file_path) as f:
        return json.load(f)


def compile_latex(file: Union[str, Path], colored: bool = False) -> None:
    """Compile a LaTeX file using pdflatex.

    Args:
        file: Path to LaTeX file
        colored: Whether this is the colored version requiring synctex
    """
    file_name = Path(file).name
    base_cmd = ["pdflatex", "-interaction=nonstopmode"]

    # Run twice for references
    for _ in range(2):
        subprocess.run(base_cmd + [file_name], timeout=1000, stdout=subprocess.DEVNULL)

    # Additional run with synctex for colored version
    if colored:
        subprocess.run(
            base_cmd + ["-synctex=1", file_name],
            timeout=1000,
            stdout=subprocess.DEVNULL,
        )


def pdf2jpg(pdf_path: Union[str, Path], output_directory: Union[str, Path]) -> None:
    """Convert PDF pages to JPG images.

    Args:
        pdf_path: Input PDF file path
        output_directory: Output directory for JPG files

    Output files are named: thread-000x-yz.jpg
    where x is thread index and yz is page number
    """
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf2image.convert_from_path(
        pdf_path,
        fmt="jpg",
        output_folder=str(output_dir),
        output_file=generators.counter_generator(prefix="thread-", suffix="-page"),
    )


def convert_pdf_figure_to_png_image(
    pdf_image: Union[str, Path], png_image: Union[str, Path], dpi: int = 72
) -> None:
    """Convert PDF figure to PNG image.

    Args:
        pdf_image: Input PDF file path
        png_image: Output PNG file path
        dpi: Resolution for conversion
    """
    # Crop PDF
    subprocess.run(
        ["pdfcrop", str(pdf_image), str(pdf_image)], stdout=subprocess.DEVNULL
    )

    # Convert to PNG
    images = pdf2image.convert_from_path(pdf_image, dpi=dpi)
    images[0].save(png_image)


def convert_eps_image_to_pdf_image(
    eps_image_path: Union[str, Path], pdf_image_path: Union[str, Path]
) -> None:
    """Convert EPS image to PDF.

    Args:
        eps_image_path: Input EPS file path
        pdf_image_path: Output PDF file path
    """
    subprocess.run(["epspdf", str(eps_image_path), str(pdf_image_path)])


def export_to_coco(
    layout_info: Dict[int, List[Block]],
    image_infos: Dict[int, Dict[str, Any]],
    file_path: Union[str, Path],
) -> None:
    """Export layout and image info to COCO format JSON.

    Args:
        layout_info: Page index to list of Block objects mapping
        image_infos: Page index to image info mapping
        file_path: Output JSON file path

    See: https://cocodataset.org/#format-data
    """
    result = {
        "info": config.config["coco_info"],
        "licenses": config.config["coco_licenses"],
        "images": _build_coco_images(layout_info, image_infos),
        "annotations": _build_coco_annotations(layout_info),
        "categories": _build_coco_categories(),
    }
    export_to_json(result, file_path)


def _build_coco_categories() -> List[Dict[str, Any]]:
    """Build COCO format category information."""
    return [
        {"id": index, "name": category, "supercategory": supercategory}
        for index, category, supercategory in config.config["category_name"]
    ]


def _build_coco_images(
    layout_info: Dict[int, List[Block]], image_infos: Dict[int, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Build COCO format image information."""
    return [
        {
            "id": page_index,
            "width": image_infos[page_index]["width"],
            "height": image_infos[page_index]["height"],
            "file_name": image_infos[page_index]["file_name"],
            **config.config["coco_image_info"],
        }
        for page_index in layout_info
    ]


def _build_coco_annotations(
    layout_info: Dict[int, List[Block]]
) -> List[Dict[str, Any]]:
    """Build COCO format annotation information."""
    annotations = []
    for page_index, page_elements in layout_info.items():
        for index, element in enumerate(page_elements):
            width, height = element.width, element.height
            annotations.append(
                {
                    "id": index,
                    "image_id": page_index,
                    "category_id": element.category,
                    "segmentation": [],
                    "bbox": [element.bbox[0], element.bbox[1], width, height],
                    "area": width * height,
                    "iscrowd": 0,
                }
            )
    return annotations


def colorize(text: str, category_name: str) -> str:
    """Colorize text based on category.

    Args:
        text: Text to colorize
        category_name: Category determining color

    Returns:
        Colorized LaTeX text

    Raises:
        NotImplementedError: For unknown categories
    """
    color = config.name2color[category_name]

    # Simple wrapping
    if category_name in {"Table", "Title", "List", "Code"}:
        return f"{{\\color{{{color}}}{text}}}"

    # Text coloring
    if category_name in {"Text", "Text-EQ"}:
        return f"{{\\textcolor{{{color}}}{{{text}}}}}"

    # Complex cases
    if category_name in {"Caption", "Footnote"}:
        index = text.find("{")
        return f"{text[:index + 1]}{{\\color{{{color}}}{text[index + 1:]}}}"

    if category_name == "Algorithm":
        prefix = text.find("\\", len("\\begin{algorithm}"))
        suffix = text.find("\\end{algorithm}")
        return (
            f"{text[:prefix]}{{\\color{{{color}}}{text[prefix:suffix]}}}{text[suffix:]}"
        )

    if category_name == "PaperTitle":
        index = text.find("{")
        return f"{text[:index + 1]}{{\\textcolor{{{color}}}{{{text[index + 1:]}}}}}"

    if category_name == "Equation":
        return f"{{\\color{{{color}}}{{{text}}}}}"

    if category_name == "Abstract":
        prefix = len("\\begin{abstract}")
        return f"{{{text[:prefix]}\\color{{{color}}}{text[prefix:]}}}"

    raise NotImplementedError(f"Invalid category name: {category_name}")


def extract_main_content(tex_file: str) -> Tuple[str, int, int]:
    """Extract the main content from a LaTeX file.

    Args:
        tex_file: Path to the LaTeX file

    Returns:
        Tuple containing:
        - Main content between document tags
        - Start position of main content in file
        - End position of main content in file

    Raises:
        ValueError: If document tags not found
    """
    with open(tex_file) as f:
        content = f.read()

    start = content.find("\\begin{document}")
    end = content.find("\\end{document}")

    if start == -1 or end == -1:
        raise ValueError("Document tags not found")

    start += len("\\begin{document}")
    main_content = content[start:end]

    return main_content, start, end


def data_from_tex_file(tex_file: str) -> Tuple[List[Union[dict, str]], int, int]:
    """Extract data from a TeX file using TexSoup.

    Args:
        tex_file: Path to the TeX file

    Returns:
        Tuple containing:
        - Extracted data as list
        - Start position of main content in file
        - End position of main content in file
    """
    main_content, start, end = extract_main_content(tex_file)
    tex_tree = TexSoup(main_content).expr.all
    data = conversion.to_list(tex_tree)

    return data, start, end


def tex_file_from_data(
    data: List[Union[dict, str]],
    tex_file: Union[str, Path],
    start: int = 0,
    end: int = -1,
) -> None:
    """Generate a TeX file from TexSoup data.

    Args:
        data: Data to convert to LaTeX
        tex_file: Output TeX file path
        start: Start position for content replacement
        end: End position for content replacement
    """
    with open(tex_file, "r") as f:
        content = f.read()

    rendered_tex = conversion.to_latex(data)
    content = content[:start] + rendered_tex + content[end:]

    with open(tex_file, "w") as f:
        f.write(content)


def replace_nth(string: str, old: str, new: str, n: int) -> str:
    """Replace the n-th occurrence of a substring.

    Args:
        string: Original string
        old: Substring to replace
        new: Replacement substring
        n: Which occurrence to replace (1-based)

    Returns:
        Modified string with n-th occurrence replaced

    Example:
        >>> replace_nth("Hello, hello, hello!", 'hello', 'hi', 2)
        'Hello, hello, hi!'
    """
    index = string.find(old)
    count = int(index != -1)

    while index != -1 and count != n:
        index = string.find(old, index + 1)
        count += 1

    if count == n:
        return string[:index] + new + string[index + len(old) :]

    return string


def find_env(wrapped_env: dict, query: List[str]) -> Optional[str]:
    """Find first matching environment variable from query list.

    Args:
        wrapped_env: Dictionary of environment variables
        query: List of environment variables to search for

    Returns:
        First matching environment variable or None
    """
    return next((env for env in query if env in wrapped_env), None)


def is_text_eq(text: str) -> bool:
    """Check if text contains mathematical expressions.

    Args:
        text: Text to check

    Returns:
        True if contains math expressions, False otherwise

    Reference:
        https://www.overleaf.com/learn/latex/Mathematical_expressions
    """
    pattern = r"(\\\(.*?\\\))|(\$.*?\$)|(\\begin\{math\}.*?\\end\{math\})"
    matches = re.findall(pattern, text)

    return any(not re.search(r"\\\$", match[0]) for match in matches)
