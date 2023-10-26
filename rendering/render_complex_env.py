from collections import defaultdict
import os
import shutil
import argparse
from typing import Tuple
import re

import rendering.utils as utils
import logger.logger as logger
from rendering import envs

log = logger.get_logger(__name__)


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


def render_env(tex_file, text_annotation, env):
    suffix = "_white.tex"
    base_name = tex_file[: -len(suffix)]
    # base_name = os.path.splitext(tex_file)[0]

    num_items = len(text_annotation[env])
    for i in range(num_items):
        output_file = base_name + "_" + env + "_" + str(i) + ".tex"
        shutil.copyfile(tex_file, output_file)

        with open(output_file, "r") as f:
            content = f.read()

        # the first one is the color definition, skip it
        new_content = replace_nth(content, env + "_color", "black", i + 2)

        log.debug(f"output_file: {output_file}")

        with open(output_file, "w") as f:
            f.write(new_content)
    return base_name


def modify_color_definitions(input_file, output_file):
    # Read the content of the input file
    with open(input_file, "r") as file:
        content = file.read()

    # Define the pattern to match the color definitions
    pattern = r"\\definecolor{([^}]+)}{RGB}{(\d+), (\d+), (\d+)}"

    # Replace the color definitions with pure white
    modified_content = re.sub(
        pattern, r"\\definecolor{\1}{RGB}{255, 255, 255}", content
    )

    # Write the modified content to the output file
    with open(output_file, "w") as file:
        file.write(modified_content)


def run(origin_tex_file):
    original_dir = os.path.dirname(origin_tex_file)
    file_name = os.path.splitext(os.path.basename(origin_tex_file))[0]

    # save a white complex env for complex env bb generation
    tex_file = os.path.join(original_dir, file_name + "_rendered_colored.tex")
    log.debug(f"tex_file: {tex_file}")
    white_tex_file = os.path.join(original_dir, file_name + "_rendered_white.tex")
    log.debug(f"white_tex_file: {white_tex_file}")
    modify_color_definitions(tex_file, white_tex_file)

    # load the text annotation information
    text_file = os.path.join(original_dir, "output/result/" + "texts.json")
    text = utils.load_json(text_file)
    text_annotation = defaultdict(list)
    for key, value in text.items():
        text_annotation[key].extend(value)
    log.debug(f"text_annotation: {text_annotation}")

    # render complex env
    for env in envs.complex_env_list:
        render_env(white_tex_file, text_annotation, env)
