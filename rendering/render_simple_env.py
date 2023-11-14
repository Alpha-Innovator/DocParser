from collections import defaultdict
import os
import re
import shutil
from typing import Union, List
from TexSoup.TexSoup.data import TexEnv
from TexSoup.app import conversion
import logger.logger as logger
from rendering import utils
from config import envs

from config import config
from TexSoup.TexSoup import TexSoup

log = logger.get_logger(__name__)

# an latex env will be parsed into a list with 3 elements
# [{'begin': xxx}, [yyy], {'end': xxx}]
# the content is in the second item, which is a list
CONTENT_INDEX = 1


texts = defaultdict(list)


def find_env(wrapped_env: dict, query: List[str]) -> Union[str, None]:
    """
    Finds and returns the environment variable from the given query list
    that exists in the wrapped_env dictionary.

    Parameters:
        wrapped_env (dict): A dictionary containing environment variables
            as keys.
        query (list): A list of environment variables to search for.

    Returns:
        Union[str, None]: The environment variable found in the query list
            that exists in the wrapped_env dictionary, or None
            if no matching environment variable is found.
    """
    for env in query:
        if env in wrapped_env:
            return env

    return None


def add_color_definition(latex_file):
    with open(latex_file, "r") as f:
        content = f.read()

    definitions = ["\n\\usepackage{xcolor}"]
    for name, rgb_color in config.name2rgbcolor.items():
        color_name = config.name2color[name]
        r, g, b = rgb_color
        definition = f"\\definecolor{{{color_name}}}{{RGB}}{{{r}, {g}, {b}}}"
        definitions.append(definition)

    color_definitions = "\n".join(definitions)

    # Find location to insert package
    package_re = r"(\\documentclass.+?)\n"
    match = re.search(package_re, content)
    if not match:
        raise ValueError("Document class not found")

    package_loc = match.end()

    # Insert package line
    content = content[:package_loc] + color_definitions + content[package_loc:]

    # Write updated content
    with open(latex_file, "w") as f:
        f.write(content)


def enclose_title(data, color="red") -> None:
    # TODO: add title rendering
    pass
    # for item in data:
    #     if not isinstance(item, dict):
    #         continue

    # env = find_env(item, envs.title_envs)
    # if env is None:
    #     for key, value in item.items():
    #         if not isinstance(value, list):
    #             continue
    #         enclose_title(value[CONTENT_INDEX], color)

    # texts["Title"].append(item[env])
    # item[env] = r"\color{" + color + "}{" + item[env] + "}"


def enclose_section(data, color="red") -> None:
    """
    Encloses a section of data in curly braces with a specified color.

    Parameters:
        data (dict): The data to be enclosed.
        color (str, optional): The color of the enclosed section.
            Defaults to 'red'.

    Returns:
        dict: A dictionary representing the enclosed section.

    Raises:
        Exception: If a 'section' or 'subsection' key is not found in the data.
    """
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.section_envs)
        if env is None:
            continue

        texts["Title"].append(item[env])
        title_text = item[env][len(env) + 2 : -1]
        item[env] = "\\" + env + "{" + r"\textcolor{" + color + "}{" + title_text + "}}"


def enclose_list(data: List, color: str = "yellow") -> None:
    """
    Encloses dictionary items in a list with a brace group
    and modifies the data in-place.

    Args:
        data (List): The list of items to be processed.
        color (str, optional): The color to be applied to the enclosed items.
            Defaults to "yellow".

    Returns:
        None
    """

    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.list_envs)
        if env is None:
            for key, value in item.items():
                if not isinstance(value, list):
                    continue
                enclose_list(value[CONTENT_INDEX], color)
            continue

        texts["List"].append(item[env])
        item[env] = r"{\color{" + color + "}{" + item[env] + "}}"


def enclose_caption(data, color="orange") -> None:
    """
    Encloses the caption of each item in the given data with color formatting.

    Args:
        data (list): A list of items.
        color (str, optional): The color to use for the caption formatting.
            Defaults to 'orange'.

    Returns:
        None

    Raises:
        None
    """
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.caption_envs)
        if env is None:
            for key, value in item.items():
                if not isinstance(value, list):
                    continue
                enclose_caption(value[CONTENT_INDEX], color)
            continue

        texts["Caption"].append(item[env])
        item[env] = r"\color{" + color + "}{" + item[env] + "}"


def enclose_equation(data, color="green") -> None:
    """
    Encloses equations in the given data with a specified color.

    Parameters:
        - data (List[Union[dict, str]]): The data containing equations to enclose.
        - color (str): The color to apply to the enclosed equations. Default is 'green'.

    Returns:
        None
    """
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.math_envs)

        if env is None:
            for key, value in item.items():
                if not isinstance(value, list):
                    continue
                enclose_equation(value[CONTENT_INDEX], color)
            continue

        texts["Equation"].append(item[env])
        item[env] = r"{\color{" + color + "}{" + item[env] + "}}"


def enclose_tabular(data: List, color="cyan"):
    """
    Generate a color brace group that encloses a tabular
    environment with a specified color

    Args:
        data (list): The data to be processed.
        color (str, optional): The color to be used. Defaults to "cyan".

    Returns:
        None
    """
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.tabular_envs)
        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_tabular(value[CONTENT_INDEX], color)
            continue

        texts["Table"].append(item[env])
        item[env] = r"{\color{" + color + "}{" + item[env] + "}}"


def enclose_footnote(data, color="red") -> None:
    """
    Encloses the text of footnotes in a given data structure
    with a specified color.

    Args:
        data (list): A list of items to be processed.
            Each item can be a dictionary.
        color (str): The color to be applied to the enclosed footnotes.
            Defaults to "red".

    Returns:
        None

    Raises:
        None
    """
    for index, item in enumerate(data):
        if not isinstance(item, str):
            if not isinstance(item, dict):
                continue
            for key, value in item.items():
                if key.lower() not in envs.text_envs:
                    continue
                if not isinstance(value, list):
                    continue
                enclose_footnote(value[CONTENT_INDEX], color)
            continue

        env_name = None
        for env in envs.footnote_envs:
            if env in item:
                env_name = env
                break

        if env_name is None:
            continue

        parsed = TexSoup(item).expr.all
        for element in parsed:
            if element.name not in envs.footnote_envs:
                continue

            extra_len = 2
            footnote = str(element.args[0])
            if len(element.args) > 1:
                extra_len += len(str(element.args[0]))
                footnote = str(element.args[1])

            texts["Footnote"].append(str(element))
            color_footnote = r"\color{" + color + "}" + footnote

            if len(element.args) > 1:
                element.args[1].string = color_footnote
            else:
                element.args[0].string = color_footnote

        data[index] = conversion.to_latex(conversion.to_list(parsed))


def is_text_eq(text: str):
    """
    Check if the given text is equal to a specific expression.

    Args:
        text (str): The text to be checked.

    Returns:
        bool: True if the text is equal to the expression, False otherwise.

    Reference:
        https://www.overleaf.com/learn/latex/Mathematical_expressions
        See also: TexSoup/TexSoup/data.py, TexMathModeEnv, TexMathEnv
    """
    parsed = TexSoup(text).expr.all

    for element in parsed:
        if not isinstance(element, TexEnv):
            continue
        if element.name in ["math", "$"]:
            return True

    return False


def enclose_text(data, text_color="olive", text_eq_color="green") -> None:
    for index, item in enumerate(data):
        if not isinstance(item, str):
            if not isinstance(item, dict):
                continue
            for key, value in item.items():
                if key.lower() not in envs.text_envs:
                    continue
                if not isinstance(value, list):
                    continue
                enclose_text(value[CONTENT_INDEX], text_color, text_eq_color)
            continue

        if not item or item == "\n" or item == "\n\n" or item.isspace():
            continue

        if is_text_eq(item):
            data[index] = r"\textcolor{" + text_eq_color + "}{" + item + "}"
            texts["Text-EQ"].append(item)
        else:
            data[index] = "\\textcolor{" + text_color + "}{" + item + "}"
            texts["Text"].append(item)

        # format
        if item[0] == "\n":
            data[index] = "\n" + data[index]
        if item[-1] == "\n":
            data[index] += "\n"


def enclose_reference(data, color="violet") -> None:
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.reference_envs)
        if env is None:
            continue

        item[env] = r"{\color{" + color + "}\n" + item[env] + "}"


def extract_figures(data):
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.graphic_envs)
        if env is None:
            for key, value in item.items():
                if not isinstance(value, list):
                    continue
                extract_figures(value[CONTENT_INDEX])
            continue

        texts["Figure"].append(item[env])


def enclose_algorithm(data, color="pink"):
    """
    Generate a function comment for the given function body.

    Args:
        data (list): The data to be processed.
        color (str, optional): The color to be used. Defaults to "pink".

    Returns:
        None

    Raises:
        None
    """
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.algorithm_envs)

        if env is None:
            for key, value in item.items():
                if not isinstance(value, list):
                    continue
                enclose_algorithm(value[CONTENT_INDEX], color)
            continue

        texts["Algorithm"].append(item[env])
        item[env] = r"{\color{" + color + "}" + item[env] + "}"


def enclose_code(data, color="blue"):
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.code_envs)

        if env is None:
            for key, value in item.items():
                if not isinstance(value, list):
                    continue
                enclose_code(value[CONTENT_INDEX], color)
            continue

        texts["Code"].append(item[env])
        item[env] = r"{\color{" + color + "}" + item[env] + "}"


def render_env(main_content):
    name2color = config.name2color
    enclose_section(main_content, color=name2color["Title"])

    enclose_list(main_content, color=name2color["List"])

    enclose_caption(main_content, color=name2color["Caption"])

    enclose_equation(main_content, color=name2color["Equation"])

    enclose_tabular(main_content, color=name2color["Table"])

    enclose_footnote(main_content, color=name2color["Footnote"])

    enclose_reference(main_content, color=name2color["Reference"])

    enclose_algorithm(main_content, color=name2color["Algorithm"])

    # extract_figures(main_content)

    # enclose_code(main_content, color=name2color["Code"])

    enclose_text(
        main_content, text_color=name2color["Text"], text_eq_color=name2color["Text-EQ"]
    )


def save_texts(file="texts.json"):
    utils.export_to_json(texts, file)


def add_layout_definition(main_content: List):
    definitions = [
        "\n\n",
        {
            "message": "\\message{[vrdu_data_process: The columnwidth is: \\the\\columnwidth]}"
        },
        "\n\n",
        {
            "message": "\\message{[vrdu_data_process: The columnsep is: \\the\\columnsep]}"
        },
        "\n\n",
        {
            "message": "\\message{[vrdu_data_process: The textwidth is: \\the\\textwidth]}"
        },
        "\n\n",
        {
            "message": "\\message{[vrdu_data_process: The paperwidth is: \\the\\paperwidth]}"
        },
        "\n\n",
        {"message": "\\message{[vrdu_data_process: The hoffset is: \\the\\hoffset]}"},
        "\n\n",
        {
            "message": "\\message{[vrdu_data_process: The oddsidemargin is: \\the\\oddsidemargin]}"
        },
        "\n\n",
    ]
    main_content.extend(definitions)


def run(input_file, debug_mode=False):
    origin_dir = os.path.dirname(input_file)
    output_file = os.path.join(origin_dir, "paper" + "_colored.tex")
    shutil.copyfile(input_file, output_file)
    add_color_definition(output_file)

    main_content, start, end = utils.data_from_tex_file(output_file)
    add_layout_definition(main_content)
    render_env(main_content)

    text_file = os.path.join(origin_dir, "output/result/" + "texts.json")
    save_texts(text_file)
    utils.tex_file_from_data(main_content, output_file, start=start, end=end)
