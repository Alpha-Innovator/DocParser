import argparse
from datetime import datetime
import glob
import os
from subprocess import CalledProcessError
from typing import Dict, List
import uuid

from vrdu import utils


def augment_data(
    data: Dict, augment_way: str, output_path: str, dpi: int = 200
) -> Dict:
    # ========================================================
    # TODO: complete this part
    prefix = "\\documentclass{article}\n\\pagenumbering{gobble}\n\\begin{document}"
    suffix = r"\end{document}"
    tex_engine = "pdflatex"
    if augment_way == "bf":
        prefix = prefix + "\\bfseries{\n"
        suffix = "}\n" + suffix
    elif augment_way == "small caps":
        prefix = prefix + "\\textsc{\n"
        suffix = "}\n" + suffix
    elif augment_way == "cyklop":
        prefix = "\\documentclass{article}\n\\pagenumbering{gobble}\n\\usepackage{cyklop}}\n\\usepackage[T1]{fontenc}\n\\begin{document}\n{\\normalfont\\bfseries\n"
        suffix = "}\n" + suffix
    elif augment_way == "Atchen":
        prefix = "\\documentclass{article}\n\\pagenumbering{gobble}\n\\usepackage{fontspec}\n\\setmainfont{QTAtchen}\n\\begin{document}\n{\\normalfont\\bfseries\n"
        suffix = "}\n" + suffix
        tex_engine = "xelatex"
    else:
        raise NotImplementedError(f"Unknown augmentation method: {augment_way}")
    # ========================================================

    tex_content = prefix + data["source_code"] + suffix
    tex_file = "temp.tex"
    pdf_file = tex_file.replace("tex", "pdf")
    with open(tex_file, "w") as f:
        f.write(tex_content)

    try:
        utils.compile_latex(tex_file, tex_engine)
    except CalledProcessError:
        return {}
    if not os.path.exists(pdf_file):
        return {}
    png_filename = str(uuid.uuid4()) + ".png"
    output_png_file = os.path.join(output_path, png_filename)
    utils.convert_pdf_figure_to_png_image(pdf_file, output_png_file, dpi=dpi)
    # remove files
    files = glob.glob(f"{os.getcwd()}/temp.*")
    for file in files:
        os.remove(file)

    result = {key: value for key, value in data.items()}
    result["image_path"] = png_filename
    result["augmentation"] = augment_way
    result["added_date"] = str(datetime.today())

    return result


def augment_dataset(reading_annotations: List[Dict], output_path: str) -> None:
    augment_ways = [
        "cyklop",  # https://tug.org/FontCatalogue/cyklop/
        "bf",  # https://www.overleaf.com/learn/latex/Font_sizes%2C_families%2C_and_styles
        # "Atchen",  # https://tug.org/FontCatalogue/qtatchen/
        "small caps",  # https://www.overleaf.com/learn/latex/Font_sizes%2C_families%2C_and_styles
        # "rotate",     # TODO: rotate the tables
        # "no_lines",   # TODO: remove all lines
        # "col_pos",  # TODO: use l,c,r to change the positions of columns
    ]

    result = []

    for item in reading_annotations:
        if "quality" not in item:
            raise ValueError("This dataset hasn't been cleaned!")

        # skip non-compiable and low quality items
        if item["quality"] != "high":
            continue

        for augment_way in augment_ways:
            augment_item = augment_data(item, augment_way, output_path)
            if not augment_item:
                continue
            result.append(augment_item)

    output_json_file = os.path.join(output_path, "reading_annotation.json")
    if os.path.exists(output_json_file):
        raise FileExistsError(
            f"{output_json_file} exists, please check before overwrite it!"
        )

    utils.export_to_json(result, output_json_file)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        required=True,
        help="The path to original tabular dataset",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="The path to save the augmented tabular dataset",
    )
    args = parser.parse_args()
    dataset_path = args.path
    output_path = args.output

    reading_annotation_file = os.path.join(
        dataset_path, "clean_reading_annotation_v2.json"
    )
    if not os.path.exists(reading_annotation_file):
        raise FileNotFoundError(f"{reading_annotation_file} doesn't exist!")

    os.makedirs(output_path, exist_ok=True)

    reading_annotations = utils.load_json(reading_annotation_file)

    augment_dataset(reading_annotations, output_path)


if __name__ == "__main__":
    main()
