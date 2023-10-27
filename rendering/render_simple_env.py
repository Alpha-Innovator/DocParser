from collections import defaultdict
import os
import re
import shutil
from typing import Union, List
import logger.logger as logger
from rendering import utils
from rendering import envs

from config import config

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


def add_usepackage_command(data, package: str) -> None:
    """
    Adds a usepackage command to the given data.

    Parameters:
    - data: A list representing the document data.
    - package: The name of the package to use.

    Returns:
    None.
    """
    # find the index of documentclass
    index = -1
    for index, item in enumerate(data):
        if isinstance(item, dict) and "documentclass" in item:
            index = index
            break

    if index == -1:
        raise Exception("documentclass not found")

    # add usepackage in rendered document
    # notice: multiple inclusion will be ignored, so this addition is safe
    data.insert(index + 1, "\n")  # for clarity
    data.insert(index + 2, {"usepackage": "\\usepackage{" + package + "}"})
    data.insert(index + 3, "\n")  # for clarity


def enclose_abstract(data, title_color="red", text_color="green"):
    """
    Encloses the abstract section of a document with specified
    title and text colors.

    Parameters:
        data (list): The list representing the document structure.
        title_color (str, optional): The color of the abstract title.
            Defaults to "red".
        text_color (str, optional): The color of the abstract text.
            Defaults to "green".

    Raises:
        Exception: If the documentclass is not found.

    """
    document_index = -1
    for index, item in enumerate(data):
        if isinstance(item, dict) and "document" in item:
            document_index = index
            break

    if document_index == -1:
        raise Exception("documentclass not found")

    # enclose title with renewcommand
    data.insert(document_index, "\n")  # for clarity
    data.insert(
        document_index,
        {
            "renewcommand": f"\\renewcommand{{\\abstractname}}{{\\color{{{title_color}}}Abstract}}\n"
        },
    )
    data.insert(document_index, "\n")  # for clarity

    # enclose the content of the abstract
    main_content = data[document_index + 3]["document"][1]
    for index, item in enumerate(main_content):
        if isinstance(item, dict) and "abstract" in item:
            texts["abstract"] = item["abstract"][CONTENT_INDEX]
            item["abstract"][CONTENT_INDEX] = {
                "color": [
                    "\\color{{{}}}{{".format(text_color),
                    *item["abstract"][CONTENT_INDEX],
                    "}\n",
                ]
            }

            break

    data[document_index + 3]["document"][1] = main_content


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
    """
    Encloses the title of each dictionary item in the given data list with
        LaTeX formatting and a specified color.

    Parameters:
        data (list[dict]): A list of dictionaries containing the
            items to be modified.
        color (str): The color to use for the enclosed title.
            Defaults to 'red'.

    Returns:
        None

    Notes:
        - The function modifies the 'title' key in each dictionary item
            in the data list.
        - The function assumes that each dictionary item in the data list
            has a 'title' key.
        - The function uses LaTeX formatting to enclose the title text in
            the specified color.
    """
    for item in data:
        if isinstance(item, dict) and "title" in item:
            index = item["title"].find("\\title{")
            # 9 is the length of prefix of title text
            title_text = item["title"][index + 9 : -1]
            rendered_title = "\\title{{\\textcolor{{{}}}{{{}}}}}".format(
                color, title_text
            )
            item["title"] = rendered_title
            texts["Title"].append(title_text)


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
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.section_envs)
        if env is None:
            continue

        texts["Title"].append(item[env])
        section_text = item[env][len(env) + 2 : -1]
        rendered_section = "\\{}{{\\textcolor{{{}}}{{{}}}}}".format(
            env, color, section_text
        )
        item[env] = rendered_section


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

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.list_envs)
        if env is None:
            continue

        texts["List"].append(item[env])
        data[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [{"color": [f"\\color{{{color}}}\n", *item[env], "\n"]}],
                {"end": "}"},
            ]
        }


def enclose_caption_inside_env(data, color="orange") -> None:
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
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        if "caption" not in item:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_caption_inside_env(value[CONTENT_INDEX], color)
            continue

        texts["Caption"].append(item["caption"])
        caption_text = item["caption"][9:-1]
        rendered_caption = "\\{}{{\\textcolor{{{}}}{{{}}}}}".format(
            "caption", color, caption_text
        )
        item["caption"] = rendered_caption


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
            continue

        enclose_caption_inside_env(item[env][CONTENT_INDEX], color)


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

        if find_env(item, envs.algorithm_envs) is not None:
            continue

        env = find_env(item, envs.math_envs)

        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_equation(value[CONTENT_INDEX], color)
            continue

        texts["Equation"].append(item)
        item[env] = {
            "BraceGroup": [
                {"begin": "{"},
                [
                    {
                        "color": [
                            "\\color{{{}}}\n".format(color),
                            item[env],
                            "\n",
                        ]
                    }
                ],
                {"end": "}"},
            ]
        }


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
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.tabular_envs)
        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_tabular(value[CONTENT_INDEX], color)
            continue

        texts["Table"].append(item)
        data[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [
                    {
                        "color": [
                            "\\color{{{}}}\n".format(color),
                            *item[env],
                            "\n",
                        ]
                    }
                ],
                {"end": "}"},
            ]
        }


def enclose_table(data, color="cyan") -> None:
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.table_envs)
        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_table(value[CONTENT_INDEX], color)
            continue

        texts["Table"].append(item)
        enclose_tabular(item[env][CONTENT_INDEX], color)


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
    for item in data:
        if not isinstance(item, dict):
            continue
        env = find_env(item, envs.footnote_envs)
        if env is None:
            continue

        footnote_text = item[env][len(env) + 2 : -1]
        rendered_footnote = "\\{}{{\\color{{{}}}{{{}}}}}".format(
            env, color, footnote_text
        )
        item[env] = rendered_footnote
        texts["Footnote"].append(footnote_text)


def enclose_text(data, color="olive"):
    result = []
    current_group = []

    for item in data:
        if isinstance(item, dict):
            # check if is an environment
            if find_env(item, envs.non_text_envs) is not None:
                if current_group:
                    result.append(current_group)
                    current_group = []
                result.append(item)
            else:
                current_group.append(item)
        elif isinstance(item, str):
            if item == "\n":
                if current_group:
                    result.append(current_group)
                    current_group = []
            else:
                index = item.find("\n\n")
                # break two paragraphs
                if index != -1:
                    current_group.append(item[:index])
                    result.append(current_group)
                    current_group = []
                    result.append("\n")
                    result.append("\n")
                    current_group.append(item[index + 2 :])
                else:
                    current_group.append(item)
        else:
            raise ValueError(f"Unknown type: {type(item)}")

    if current_group:
        result.append(current_group)

    for index, item in enumerate(result):
        if isinstance(item, dict):
            continue
        if isinstance(item, str):
            continue
        # list
        texts["Text"].append(item)
        result[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [
                    {
                        "color": [
                            "\\color{{{}}}\n".format(color),
                            *item,
                            "\n",
                        ]
                    }
                ],
                {"end": "}\n"},
            ]
        }

    return result


def enclose_reference(data, color="violet") -> None:
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.reference_envs)
        if env is None:
            continue

        data[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [
                    "\n",
                    {"color": "\\color{{{}}}{{{}}}\n".format(color, item[env])},
                    "\n",
                ],
                {"end": "}"},
            ]
        }


def enclose_graphics_inside_figure(data, color="black"):
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.graphic_envs)
        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_graphics_inside_figure(value[CONTENT_INDEX], color)
        else:
            texts["Figure"].append(item[env])


def enclose_figure(data, color="black"):
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.figure_envs)
        if env is None:
            continue

        enclose_graphics_inside_figure(item[env][CONTENT_INDEX], color)


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
                if isinstance(value, list):
                    enclose_algorithm(value[CONTENT_INDEX], color)
            continue

        texts["Algorithm"].append(item)
        item[env][1].insert(0, {"color": "\n\\color{{{}}}".format(color)})


def enclose_code(data, color="blue"):
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, envs.code_envs)

        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_code(value[CONTENT_INDEX], color)
            continue

        texts["Code"].append(item)
        data[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [
                    {
                        "color": [
                            "\\color{{{}}}\n".format(color),
                            *item[env],
                            "\n",
                        ]
                    }
                ],
                {"end": "}"},
            ]
        }


def render_env(main_content):
    name2color = config.name2color

    enclose_section(main_content, color=name2color["Title"])

    enclose_list(main_content, color=name2color["List"])

    enclose_caption(main_content, color=name2color["Caption"])

    enclose_equation(main_content, color=name2color["Equation"])

    enclose_tabular(main_content, color=name2color["Table"])

    enclose_footnote(main_content, color=name2color["Footnote"])

    enclose_reference(main_content, color=name2color["Text"])

    enclose_algorithm(main_content, color=name2color["Algorithm"])

    enclose_figure(main_content, color=name2color["Figure"])

    enclose_code(main_content, color=name2color["Code"])

    # main_content = enclose_text(main_content, color=name2color["Text"])
    # data[index]["document"][1] = main_content


def save_texts(file="texts.json"):
    utils.export_to_json(texts, file)


def run(input_file, debug_mode=False):
    origin_dir = os.path.dirname(input_file)
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(origin_dir, file_name + "_rendered_colored.tex")
    shutil.copyfile(input_file, output_file)
    add_color_definition(output_file)

    main_content, start, end = utils.data_from_tex_file(output_file)
    render_env(main_content)

    text_file = os.path.join(origin_dir, "output/result/" + "texts.json")
    save_texts(text_file)
    utils.tex_file_from_data(main_content, output_file, start=start, end=end)
