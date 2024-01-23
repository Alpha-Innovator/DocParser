from datetime import datetime
from functools import partial
import glob
import multiprocessing
import os
import argparse
import re
from subprocess import CalledProcessError
from typing import Dict, List
from uuid import uuid4

from vrdu import logger
from vrdu import utils

log_file = "vrdu_table_" + str(uuid4()) + ".log"
log = logger.setup_app_level_logger(file_name=log_file, level="INFO", mode="a")


dpi = 200
output_path = "/cpfs01/shared/ADLab/datasets/vrdu_table_final_2"


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

            tex_files.append(tex_file)
    return tex_files


def expand_column_patterns(column_patterns: str) -> str:
    expanded_columns = ""
    pattern_parts = column_patterns.split("|")
    for pattern in pattern_parts:
        if pattern.startswith("*{") and pattern.endswith("}"):
            sub_pattern = pattern[2:-1]
            num, form = sub_pattern.split("}{")
            num = int(num)
            expanded_columns += form * num
        else:
            expanded_columns += pattern
        expanded_columns += "|"
    return expanded_columns.rstrip("|")


def add_layout_information(tabular: Dict):
    tabular["cols"] = 0
    tabular["rows"] = 0
    # count the number of rows and columns
    cols_match = re.search(
        r"\\begin{tabular}\n?(?:\[.*?\])?{(.*)}", tabular["source_code"]
    )

    if not cols_match:
        log.debug(f"cols not found for {tabular}")
        return tabular
    cols = cols_match.group(1)

    align_patterns = ["c", "r", "l", "p"]
    try:
        expanded_cols = expand_column_patterns(cols)
    except Exception:
        log.exception(f"Error processing data: {tabular}")
        return tabular

    num_columns = sum(expanded_cols.count(ch) for ch in align_patterns)
    tabular["cols"] = num_columns

    # count the number of rows
    num_rows = tabular["source_code"].count("\\\\")
    num_rows += tabular["source_code"].count("\\tabularnewline")
    tabular["rows"] = num_rows

    # add the count of multicolumn and multirows
    multirow_count = len(re.findall(r"\\multirow", tabular["source_code"]))
    multicolumn_count = len(re.findall(r"\\multicolumn", tabular["source_code"]))
    tabular["multirow"] = multirow_count
    tabular["multicol"] = multicolumn_count

    # mark table with <= 3 columns or rows <= 3 as low quality
    if num_columns <= 3 or num_rows <= 3:
        tabular["quality"] = "low"


def remove_cite(tex_content: str) -> str:
    # remove all cites in a string representing latex content
    # https://www.overleaf.com/learn/latex/Natbib_citation_styles
    tex_content = re.sub(r"\\cite\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\cite\*\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\citet\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\citep\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\citet\*\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\citep\*\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\citeauthor\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\citeyear\{.*?\}", "", tex_content)

    # remove ref
    # https://en.wikibooks.org/wiki/LaTeX/Labels_and_Cross-referencing
    tex_content = re.sub(r"\\ref\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\eqref\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\pageref\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\autoref\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\vref\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\cref\{.*?\}", "", tex_content)
    tex_content = re.sub(r"\\labelcref\{.*?\}", "", tex_content)

    return tex_content


def generate_annotation(tabular: str) -> Dict:
    prefix = "\\documentclass[10pt]{article}\n\\usepackage[a4paper, margin=1in]{geometry}\n\\usepackage[table,dvipsnames]{xcolor}\n\\usepackage{booktabs}\n\\usepackage{tabularx, makecell, multirow}\n\\usepackage{graphicx}\n\\usepackage{array}\n\\usepackage{longtable}\n\\usepackage{amsmath}\n\\usepackage{amssymb}\n\\usepackage{amsbsy}\n\\pagenumbering{gobble}\n\\begin{document}\n"
    suffix = "\n\\end{document}"
    data = {}

    if "\\includegraphic" in tabular:
        return data

    tabular = remove_cite(tabular)
    data["source_code"] = tabular

    tex_content = prefix + data["source_code"] + suffix
    temp_filename = str(uuid4())
    temp_file = temp_filename + ".tex"
    pdf_file = temp_file.replace("tex", "pdf")
    with open(temp_file, "w") as f:
        f.write(tex_content)

    try:
        utils.compile_latex(temp_file)
        data["quality"] = "high"
    except Exception:
        data["quality"] = "uncompiable"
        data["image_path"] = None

    png_filename = str(uuid4()) + ".png"
    output_png_file = os.path.join(output_path, png_filename)
    try:
        utils.convert_pdf_figure_to_png_image(pdf_file, output_png_file, dpi=dpi)
        data["image_path"] = png_filename
    except Exception:
        data["quality"] = "uncompiable"
        data["image_path"] = None

    if not os.path.exists(output_png_file):
        data["quality"] = "uncompiable"
        data["image_path"] = None
    data["added_date"] = str(datetime.today())

    # remove files
    files = glob.glob(f"{os.getcwd()}/{temp_filename}.*")
    for file in files:
        os.remove(file)

    add_layout_information(data)

    return data


def extract_caption(table: str):
    pattern = r"\\caption\{(.*?)\}"
    matches = re.finditer(pattern, table)
    for match in matches:
        start = match.start()
        end = match.end()

        # the regex is greedy, iterate to find the end of footnote env
        num_left_brackets = table[start:end].count("{")
        num_right_brackets = table[start:end].count("}")
        while num_right_brackets < num_left_brackets:
            if table[end] == "{":
                num_left_brackets += 1
            elif table[end] == "}":
                num_right_brackets += 1
            end += 1

        return table[start:end]

    return None


def process_one_file(tex_file):
    log.debug(f"tex_file={tex_file}")
    try:
        with open(tex_file) as f:
            tex_content = f.read()
    except UnicodeDecodeError:
        return []

    tabular_pattern = r"\\begin{tabular}.*?\\end{tabular}"
    tabular_indexes = [
        (m.start(), m.end())
        for m in re.finditer(tabular_pattern, tex_content, re.DOTALL)
    ]
    tabulars = [tex_content[index[0] : index[1]] for index in tabular_indexes]

    result = [generate_annotation(tabular) for tabular in tabulars]

    # retrive caption
    table_pattern = r"\\begin{table}.*?\\end{table}"
    table_indexes = [
        (m.start(), m.end()) for m in re.finditer(table_pattern, tex_content, re.DOTALL)
    ]

    for i, data in enumerate(result):
        data["paper_source"] = tex_file
        data["caption"] = None
        for table_index in table_indexes:
            if (
                tabular_indexes[i][0] >= table_index[0]
                and tabular_indexes[i][1] <= table_index[1]
            ):
                data["caption"] = extract_caption(
                    tex_content[table_index[0] : table_index[1]]
                )
                break

    log.info(f"Extract {len(result)} tabular data in {tex_file}")
    return result


def process_one_discpline(path, cpu_count, discpline):
    discpline_path = os.path.join(path, discpline)
    log.info(f"path to raw data: {discpline_path}")
    log.info(f"Using cpu counts: {cpu_count}")
    tex_files = extract_tex_files(discpline_path)
    log.info(f"Found {len(tex_files)} tex files")

    results = []
    try:
        with multiprocessing.Pool(cpu_count) as pool:
            parallel_results = pool.map(process_one_file, tex_files)
            results.extend(
                [
                    x
                    for parallel_result in parallel_results
                    for x in parallel_result
                    if x
                ]
            )
    except Exception:
        log.exception(f"failed to process discpline: {discpline}")
    finally:
        for x in results:
            x["discpline"] = discpline
        utils.export_to_json(
            results, os.path.join(output_path, f"reading_annotation_{discpline}.json")
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str, required=True)
    parser.add_argument("-c", "--cpu_count", type=int, required=True)
    parser.add_argument("-d", "--discpline", type=str, required=True)
    args = parser.parse_args()
    path, cpu_count, discpline = (
        args.path,
        args.cpu_count,
        args.discpline,
    )
    process_one_discpline(path, cpu_count, discpline)


if __name__ == "__main__":
    main()
