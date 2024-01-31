from datetime import datetime
import glob
import multiprocessing
import os
import argparse
import random
import re
import shutil
import subprocess
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


def extract_columns(tabular) -> int:
    # step0: extract the column field from table
    # \begin{tabular*}[]{cccccccccc}
    cols_match = re.search(r"\\begin{tabular}\n?(?:\[.*?\])?{(.*)}", tabular)

    if not cols_match:
        return 0

    col_spec = cols_match.group(1)
    if len(col_spec) == 1:
        return 1

    start = tabular.find(col_spec)
    end = start
    num_left_bracket = 1
    num_right_bracket = 0
    while num_right_bracket < num_left_bracket:
        if tabular[end] == "{":
            num_left_bracket += 1
        elif tabular[end] == "}":
            num_right_bracket += 1
        end += 1

    cols = tabular[start : end - 1]

    # step1: remove |
    cols = cols.replace("|", "")
    cols = cols.replace(" ", "")
    cols = cols.replace("\\centering", "")
    cols = cols.replace("\\arraybackslash", "")

    # step2: expand column patterns
    # step2.1 remove @{}, >{}, <{}, !{}
    for ch in ["@", ">", "<", "!"]:
        while cols.find(ch) != -1:
            result = ""
            index = cols.find(ch)
            start = index
            end = start
            num_left_bracket = 0
            num_right_bracket = 0
            while num_left_bracket == 0 or num_right_bracket < num_left_bracket:
                if cols[end] == "{":
                    num_left_bracket += 1
                elif cols[end] == "}":
                    num_right_bracket += 1
                end += 1
            if start == 0:
                result = cols[end:]
            else:
                result = cols[:start] + cols[end:]
            cols = result

    # step2.2 delete width brackets
    cols = re.sub(r"(p|m|b)\{.*?\}", r"\1", cols)
    # step2.3 expand abbreviations
    result = 0

    pattern1 = r"\*(\d+)\{(.+?)\}"
    matches = re.findall(pattern1, cols)
    for match in matches:
        num_repetitions = int(match[0])
        col_spec = match[1]
        result += (num_repetitions - 1) * len(col_spec)

    pattern2 = r"\*{(.*?)}\{(.+?)\}"
    matches = re.findall(pattern2, cols)
    for match in matches:
        num_repetitions = int(match[0])
        col_spec = match[1]
        result += (num_repetitions - 1) * len(col_spec)

    # step3: extract columns
    for c in cols:
        if c.isalpha():
            result += 1

    return result


def classify_quality(tabular_data: Dict):
    # mark table with <= 3 columns or rows <= 3 as low quality
    if not tabular_data["image_path"]:
        return
    if tabular_data["cols"] <= 3 or tabular_data["rows"] <= 3:
        tabular_data["quality"] = "low"
        return
    tabular_data["quality"] = "high"


def add_layout_information(tabular_data: Dict):
    # count the number ofcolumns
    tabular_data["cols"] = extract_columns(tabular_data["source_code"])

    # count the number of rows
    num_rows = tabular_data["source_code"].count("\\\\")
    num_rows += tabular_data["source_code"].count("\\tabularnewline")
    tabular_data["rows"] = num_rows

    # add the count of multicolumn and multirows
    multirow_count = len(re.findall(r"\\multirow", tabular_data["source_code"]))
    multicolumn_count = len(re.findall(r"\\multicolumn", tabular_data["source_code"]))
    tabular_data["multirow"] = multirow_count
    tabular_data["multicol"] = multicolumn_count


def remove_cite(tex_content: str) -> str:
    # remove all cites in a string representing latex content
    # https://www.overleaf.com/learn/latex/Natbib_citation_styles
    cite_patterns = "|".join(
        [
            r"\\cite\{.*?\}",
            r"\\cite\*\{.*?\}",
            r"\\citet\{.*?\}",
            r"\\citet\*\{.*?\}",
            r"\\citep\{.*?\}",
            r"\\citep\*\{.*?\}",
            r"\\citeauthor\{.*?\}",
            r"\\citeyear\{.*?\}",
        ]
    )
    tex_content = re.sub(cite_patterns, "", tex_content)

    # remove ref
    # https://en.wikibooks.org/wiki/LaTeX/Labels_and_Cross-referencing
    ref_patterns = "|".join(
        [
            r"\\ref\{.*?\}",
            r"\\eqref\{.*?\}",
            r"\\pageref\{.*?\}",
            r"\\autoref\{.*?\}",
            r"\\vref\{.*?\}",
            r"\\cref\{.*?\}",
            r"\\labelcref\{.*?\}",
        ]
    )
    tex_content = re.sub(ref_patterns, "", tex_content)

    return tex_content


def remove_comments(tabular: str) -> str:
    output = ""
    for line in tabular.splitlines():
        output += re.sub(r"(?<!\\)%.*?(?=$|(?<!\\)\%)", "", line, flags=re.DOTALL)
        output += "\n"

    return output


def generate_annotation(tabular_data: Dict) -> None:
    prefix = r"""
    \documentclass[10pt]{article}
    \usepackage[a3paper, margin=1in]{geometry}
    \usepackage[table,dvipsnames]{xcolor}
    \usepackage{booktabs}
    \usepackage{tabularx, tabulary, makecell, multirow}
    \usepackage{graphicx}
    \usepackage{array}
    \usepackage{hyperref}
    \usepackage{longtable}
    \usepackage{amsmath}
    \usepackage{amssymb}
    \usepackage{amsbsy}
    \pagenumbering{gobble}
    \begin{document}
    \begin{table*}[t]
    \centering

    """

    suffix = r"""

    \end{table*}
    \end{document}
    """

    tabular = tabular_data["source_code"]
    if "\\includegraphic" in tabular:
        return

    temp_filename = str(uuid4())
    temp_file = temp_filename + ".tex"
    pdf_file = temp_file.replace("tex", "pdf")
    png_filename = str(uuid4()) + ".png"
    output_png_file = os.path.join(output_path, png_filename)

    try:
        # step1: remove redundant stuff
        tabular = remove_cite(tabular)
        tabular = remove_comments(tabular)

        tabular_data["source_code"] = tabular

        # step2: compile tex into png images
        tex_content = prefix + tabular + suffix
        with open(temp_file, "w") as f:
            f.write(tex_content)

            # FIXME: add a timeout to control running time
            # utils.compile_latex(temp_file)
        subprocess.run(["pdflatex", temp_file], check=True, timeout=100)
        utils.convert_pdf_figure_to_png_image(pdf_file, output_png_file, dpi=200)
        tabular_data["image_path"] = png_filename

        # step3: add layout metadata
        add_layout_information(tabular_data)

        # step4: classify quality
        classify_quality(tabular_data)
    except Exception as e:
        error_type = e.__class__.__name__
        error_info = str(e)
        log.error(
            f"[VRDU] failed to process tabular: {tabular}, type: {error_type}, message: {error_info}"
        )
    finally:
        # remove files
        files = glob.glob(f"{os.getcwd()}/{temp_filename}.*")
        for file in files:
            os.remove(file)


def extract_caption(table: str) -> str:
    pattern = r"\\caption\{(.*?)\}"
    matches = re.finditer(pattern, table)
    for m in matches:
        start = m.start()
        end = m.end()

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

    return ""


def process_one_file(tex_file):
    log.debug(f"tex_file={tex_file}")
    result = []

    try:
        with open(tex_file) as f:
            tex_content = f.read()
    except UnicodeDecodeError:
        return result

    # use this pattern to extract all tabulars
    tabular_pattern = "|".join(
        [
            r"\\begin{tabular}.*?\\end{tabular}",
            r"\\begin{tabular*}.*?\\end{tabular*}",
            r"\\begin{tabularx}.*?\\end{tabularx}",
            r"\\begin{tabulary}.*?\\end{tabulary}",
        ]
    )

    # use this pattern to find all caption
    table_pattern = "|".join(
        [
            r"\\begin{table}.*?\\end{table}",
            r"\\begin{table*}.*?\\end{table*}",
            r"\\begin{wraptable}.*?\\end{wraptable}",
        ]
    )

    tabular_indexes = [
        (m.start(), m.end())
        for m in re.finditer(tabular_pattern, tex_content, re.DOTALL)
    ]
    tabulars = [tex_content[index[0] : index[1]] for index in tabular_indexes]

    if not tabulars:
        return result

    table_indexes = [
        (m.start(), m.end()) for m in re.finditer(table_pattern, tex_content, re.DOTALL)
    ]
    captions = [
        (
            start,
            end,
            extract_caption(tex_content[start:end]),
        )
        for start, end in table_indexes
    ]

    for index, tabular in enumerate(tabulars):
        log.info(f"processing tabular: {tabular}")
        data = {
            "source_code": tabular,
            "paper_source": tex_file,
            "caption": None,
            "quality": "uncompiable",
            "image_path": None,
            "added_date": str(datetime.today()),
            "cols": 0,
            "rows": 0,
            "multicol": 0,
            "multirow": 0,
        }
        generate_annotation(data)

        # try to retrive caption
        for start, end, caption in captions:
            if tabular_indexes[index][0] >= start and tabular_indexes[index][1] <= end:
                data["caption"] = caption
                break

        result.append(data)

    log.info(f"Extract {len(result)} tabular data in {tex_file}")
    return result


def process_one_discpline(path, cpu_count, discpline):
    discpline_path = os.path.join(path, discpline)
    log.info(f"path to raw data: {discpline_path}")
    log.info(f"Using cpu counts: {cpu_count}")
    tex_files = extract_tex_files(discpline_path)
    log.info(f"Found {len(tex_files)} tex files")

    json_file = os.path.join(output_path, f"reading_annotation_{discpline}.json")

    # use existed source to filter processed tex files
    existed_json_file = os.path.join(
        output_path, f"{discpline}/reading_annotation_{discpline}.json"
    )
    existed_source = set()
    if os.path.exists(existed_json_file):
        existed_json_data = utils.load_json(existed_json_file)
        existed_source = set(
            x["paper_source"] for x in existed_json_data if "paper_source" in x
        )
    if os.path.exists(json_file):
        existed_json_data = utils.load_json(json_file)
        existed_source.union(
            set(x["paper_source"] for x in existed_json_data if "paper_source" in x)
        )
    unique_tex_files = [x for x in tex_files if x not in existed_source]
    random.shuffle(unique_tex_files)

    log.info(f"Extract table from {len(unique_tex_files)} tex files")

    try:
        # use mini-batch to prevent memory overflow
        slice_length = 100
        for i in range(0, len(unique_tex_files), slice_length):
            batch_tex_files = unique_tex_files[i : i + slice_length]
            with multiprocessing.Pool(cpu_count) as pool:
                # results = pool.map(process_one_file, batch_tex_files)
                results = pool.map_async(process_one_file, batch_tex_files)
                results = results.get(timeout=300)  # Timeout value in seconds

            # filter all empty items
            results = [x for result in results for x in result if x]
            log.info(f"there are {len(results)} items")

            for x in results:
                x["discpline"] = discpline

            # use append mode to update json file
            json_data = []
            if os.path.exists(json_file):
                json_data = utils.load_json(json_file)

            json_data.extend(results)
            utils.export_to_json(json_data, json_file)

            log.info(f"processed {i,i + slice_length}-th batch")
    except Exception:
        log.error(f"failed to process discpline: {discpline}")
    finally:
        shutil.move(log_file, f"vrdu_table_{discpline}.log")


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
