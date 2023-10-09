import os
import shutil
import argparse
from typing import Tuple

import rendering.utils as utils
import logger.logger as logger

log = logger.setup_app_level_logger(file_name="app_debug.log")


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


def parse_arguments() -> Tuple[str, str]:
    """
    Parse the command-line arguments

    Returns:
        str: The path to the tex file.
        str: The path to the text annotation file.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex_file", type=str, help="The path to the tex file")
    parser.add_argument(
        "--text_annotation_file", type=str, help="The path to the text annotation file"
    )
    args = parser.parse_args()
    tex_file, text_annotation_file = args.tex_file, args.text_annotation_file
    return tex_file, text_annotation_file


def render_env(tex_file, text_annotation, env_name):
    base_name = os.path.splitext(tex_file)[0]

    num_algorithms = len(text_annotation[env_name])
    for i in range(num_algorithms):
        output_file = base_name + "_" + env_name + "_" + str(i) + ".tex"
        shutil.copyfile(tex_file, output_file)

        with open(output_file, "r") as f:
            content = f.read()

        # the first one is the color definition, skip it
        new_content = replace_nth(
            content, env_name.capitalize() + "_color", "black", i + 2
        )

        with open(output_file, "w") as f:
            f.write(new_content)
    return base_name


def run(tex_file, text_file):
    text_annotation = utils.data_from_tex_file(text_file)
    env_list = ["algorithm", "equation", "table"]
    for env in env_list:
        render_env(tex_file, text_annotation, env)
