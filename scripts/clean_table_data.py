import glob
import os
import re
import shutil
from typing import Dict
from uuid import uuid4
import pandas as pd
from PIL import Image


from vrdu import logger
from vrdu import utils

log_file = "vrdu_table_clean" + ".log"
log = logger.setup_app_level_logger(file_name=log_file, level="INFO")


total_df = pd.read_csv("scripts/batch_count.csv")
prefix = "reading_annotation_"
suffix = ".json"
table_data_df = pd.read_csv("scripts/table_data_count.csv")


def extract_columns(tabular):
    # step0: extract the column field from table
    # \begin{tabular*}[]{cccccccccc}
    log.debug(f"tabular={tabular}")
    cols_match = re.search(r"\\begin{tabular}\n?(?:\[.*?\])?{(.*)}", tabular)

    if not cols_match:
        return 0

    col_spec = cols_match.group(1)
    if len(col_spec) == 1:
        return 1

    log.debug(f"match={col_spec}")
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
    log.debug(f"cols={cols}")

    # step1: remove |
    cols = cols.replace("|", "")
    cols = cols.replace(" ", "")
    cols = cols.replace("\\centering", "")
    cols = cols.replace("\\arraybackslash", "")

    # step2: expand column patterns
    # step2.1 remove @{}
    while cols.find("@") != -1:
        result = ""
        index = cols.find("@")
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
        log.debug(f"1 type match={match[0]}")
        num_repetitions = int(match[0])
        col_spec = match[1]
        result += (num_repetitions - 1) * len(col_spec)

    pattern2 = r"\*{(.*?)}\{(.+?)\}"
    matches = re.findall(pattern2, cols)
    for match in matches:
        log.debug(f"2 type match={match[0]}")
        num_repetitions = int(match[0])
        col_spec = match[1]
        result += (num_repetitions - 1) * len(col_spec)

    # step3: extract columns
    for c in cols:
        if c.isalpha():
            result += 1

    return result


def remove_comment(x: Dict):
    output = ""
    content = x["source_code"]

    for line in content.splitlines():
        output += re.sub(r"(?<!\\)%.*?(?=$|(?<!\\)\%)", "", line, flags=re.DOTALL)
        output += "\n"

    return output


def update_image_for_large_table(source_code, image_path, dpi=200):
    log.info(f"{image_path} starts processing.")
    prefix = "\\documentclass[10pt]{article}\n\\usepackage[a3paper, margin=1in]{geometry}\n\\usepackage[table,dvipsnames]{xcolor}\n\\usepackage{tikz}\n\\usepackage{booktabs}\n\\usepackage{tabularx, makecell, multirow}\n\\usepackage{graphicx}\n\\usepackage{array}\n\\usepackage{longtable}\n\\usepackage{amsmath}\n\\usepackage{amssymb}\n\\usepackage{amsbsy}\n\\pagenumbering{gobble}\n\\begin{document}\n\\begin{table*}[t]\n\\centering\n\\scalebox{0.9}{\n"
    suffix = "\n}\n\\end{table*}\n\\end{document}"

    tex_content = prefix + source_code + suffix
    temp_filename = str(uuid4())
    temp_file = temp_filename + ".tex"
    pdf_file = temp_file.replace("tex", "pdf")
    with open(temp_file, "w") as f:
        f.write(tex_content)

    try:
        utils.compile_latex(temp_file)
        utils.convert_pdf_figure_to_png_image(pdf_file, image_path, dpi=dpi)
        files = glob.glob(f"{os.getcwd()}/{temp_filename}.*")
        for file in files:
            os.remove(file)
        log.info(f"{image_path} has been updated.")
    except Exception:
        log.error(f"failed to process {image_path}")


def scale_large_tables():
    database_df_file = (
        "/cpfs01/shared/ADLab/datasets/vrdu_table_final_2/table_database.csv"
    )
    database_df = pd.read_csv(database_df_file)

    large_table_df = database_df[database_df["image_width"] == 2100]
    for index, row in large_table_df.iterrows():
        image_path = row["image_path"]
        with Image.open(image_path) as image:
            width, height = image.size
            large_table_df.at[index, "image_height"] = height
            large_table_df.at[index, "image_width"] = width

    unprocessed_df = large_table_df[large_table_df["image_width"] == 2100].sample(
        frac=1.0
    )
    log.info(
        f"start processing, there are {len(unprocessed_df)} items after pre-processing {len(large_table_df)} items"
    )
    for index, row in unprocessed_df.iterrows():
        source_code = row["source_code"]
        image_path = row["image_path"]
        log.info(f"index: {index}, image_path: {image_path}")
        update_image_for_large_table(source_code, image_path)


def main():
    main_path = "/cpfs01/shared/ADLab/datasets/vrdu_table_final_2"

    for discpline in list(table_data_df["discpline"].values):
        # for discpline in ["cs.SC"]:
        modified_terms = 0
        discpline_path = os.path.join(main_path, discpline)
        json_file = os.path.join(discpline_path, prefix + discpline + suffix)

        if not os.path.exists(json_file):
            continue

        log.debug(f"json_file={json_file}")
        json_data = utils.load_json(json_file)

        # use robust way to parse columns
        # update_columns(modified_terms, json_data)
        # delete data that has no images
        # result = [x for x in json_data if "image_path" in x and x["image_path"]]
        # log.info(
        #     f"before processing: {len(json_data)}, after processing: {len(result)}"
        # )
        for x in json_data:
            output = remove_comment(x)

            if x["source_code"] != output:
                modified_terms += 1

            x["source_code"] = output

        utils.export_to_json(json_data, json_file)

        log.info(f"modify {modified_terms} items in {discpline}")


def update_columns(modified_terms, json_data):
    for x in json_data:
        if "source_code" not in x:
            continue
        try:
            modified_columns = extract_columns(x["source_code"])
        except Exception:
            log.exception(f"error processing image file: {x['image_path']}")
            continue
        quality = x["quality"]
        x["cols"] = modified_columns
        if x["cols"] <= 3 or x["rows"] <= 3:
            if x["image_path"]:
                x["quality"] = "low"
        else:
            if x["image_path"]:
                x["quality"] = "high"

        if quality != x["quality"]:
            modified_terms += 1
            log.info(
                f"after processing: image: {x['image_path']}, cols: {x['cols']}, rows: {x['rows']}, quality: {x['quality']}"
            )


if __name__ == "__main__":
    # main()
    scale_large_tables()
