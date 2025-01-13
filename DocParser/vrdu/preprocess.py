import re
from pathlib import Path
from typing import Optional
from loguru import logger

from DocParser.arxiv_cleaner.cleaner import Cleaner
from DocParser.vrdu.config import envs, config
from DocParser.vrdu import utils


def remove_comments(tex_file: Path) -> None:
    """
    Removes LaTeX comments from a TeX file.

    Args:
        tex_file: Path to the TeX file
    """
    tex_file = Path(tex_file)
    content = tex_file.read_text()

    # Remove LaTeX comments
    pattern = r"\\begin{comment}(.*?)\\end{comment}"
    content = re.sub(pattern, "", content, flags=re.DOTALL)

    tex_file.write_text(content)


def clean_tex(tex_file: Path) -> None:
    """
    Clean the given TeX file using arxiv-cleaner.

    Args:
        tex_file: Path to the TeX file
    """
    tex_file = Path(tex_file)
    main_directory = tex_file.parent

    # Create and run the cleaner
    cleaner = Cleaner(
        input_dir=str(main_directory),
        output_dir=str(main_directory),
        tex=tex_file.name,
        command_options=config.command_options,
        verbose=False,
    )
    cleaner.clean()

    # Remove any remaining comments
    remove_comments(tex_file)


def get_graphics_path(content: str) -> str:
    """Extract graphics path from LaTeX content."""
    pattern = r"\\graphicspath\{\{(.+?)}"
    if match := re.search(pattern, content, re.DOTALL):
        return match.group(1)
    return ""


def convert_image(
    image_path: Path, main_dir: Path, graphics_path: str, target_ext: str = ".png"
) -> Optional[str]:
    """
    Convert image to target format if needed.
    Returns the new image name or None if conversion failed.
    """
    if not image_path.exists():
        logger.error(f"File not found: {image_path}")
        return None

    if image_path.suffix in [".eps", ".ps"]:
        # Convert eps/ps to pdf first
        pdf_path = image_path.with_suffix(".pdf")
        utils.convert_eps_image_to_pdf_image(image_path, pdf_path)
        image_path = pdf_path

    if image_path.suffix == ".pdf":
        # Convert pdf to png
        png_path = image_path.with_suffix(".png")
        utils.convert_pdf_figure_to_png_image(image_path, png_path)
        return png_path.name

    return image_path.name


def replace_pdf_ps_figures_with_png(tex_file: Path) -> None:
    """
    Replace PDF, PS, EPS figures with PNG figures in a TeX file
    to support pdfminer detecting bounding box.

    Args:
        tex_file: Path to the TeX file

    Raises:
        FileNotFoundError: If an image file is not found
    """
    tex_file = Path(tex_file)
    main_directory = tex_file.parent
    content = tex_file.read_text()

    graphics_path = get_graphics_path(content)

    # Replace \psfig and \epsfig with \includegraphics
    content = re.sub(r"\\psfig{([^}]*)}", r"\\includegraphics{\1}", content)
    content = re.sub(r"\\epsfig{([^}]*)}", r"\\includegraphics{\1}", content)

    # Find all \includegraphics commands
    pattern = r"\\includegraphics(\[.*?\])?\{(.*?)\}"
    matches = re.findall(pattern, content)

    # Supported extensions
    ext_patterns = [".eps", ".ps", ".jpg", ".jpeg", ".png", ".pdf"]

    # Process each image
    for _, img_path in matches:
        image_name = img_path

        # Add extension if missing
        if not any(ext in image_name for ext in ext_patterns):
            for ext in ext_patterns:
                test_path = Path(main_directory, graphics_path, image_name).with_suffix(
                    ext
                )
                if test_path.exists():
                    image_name = f"{image_name}{ext}"
                    break

        # Skip if already in supported format
        if any(ext in image_name for ext in [".jpg", ".jpeg", ".png"]):
            content = content.replace(img_path, image_name)
            continue

        # Convert image if needed
        image_path = Path(main_directory, graphics_path, image_name)
        if new_name := convert_image(image_path, main_directory, graphics_path):
            content = content.replace(img_path, new_name)

    tex_file.write_text(content)


def delete_table_of_contents(tex_file: Path) -> None:
    """
    Delete table of contents, list of figures/tables/algorithms.

    Args:
        tex_file: Path to the TeX file
    """
    tex_file = Path(tex_file)
    content = tex_file.read_text()

    pattern = r"\\(" + "|".join(envs.table_of_contents) + r")"
    content = re.sub(pattern, "", content)

    tex_file.write_text(content)


def run(tex_file: Path) -> None:
    """
    Preprocess a LaTeX document by:
    1. Cleaning with arxiv_cleaner
    2. Converting figures to PNG format
    3. Removing table of contents

    Args:
        tex_file: Path to the LaTeX document
    """
    clean_tex(tex_file)
    replace_pdf_ps_figures_with_png(tex_file)
    delete_table_of_contents(tex_file)
