from ast import Dict
from typing import Union, List, Dict, Tuple
import logger.logger as logger
from rendering.utils import export_to_json

log = logger.get_logger(__name__)

# an latex env will be parsed into a list with 3 elements
# [{'begin': xxx}, [yyy], {'end': xxx}]
# the content is in the second element, which is a list
CONTENT_INDEX = 1

# colors in xcolor.sty:
# [red, green,blue, cyan, magenta, yellow, black, gray, white,
# darkgray, lightgray, brown, lime, olive, orange, pink,
# purple, teal, violet.]


math_envs = ["equation", "align", "equation*", "align*", "$$"]
table_envs = ["table", "table*"]
figure_envs = ["figure", "minipage", "subfigure"]
algorithm_envs = [
    "algorithm",
    "algorithm*",
    "algorithmic",
    "algorithmic*",
    "algorithm2e",
]
list_envs = ["itemize", "enumerate"]
reference_envs = ["bibliography"]
caption_envs = table_envs + figure_envs
footnote_envs = ["footnote", "footnote*", "footnote**"]
non_text_envs = (
    math_envs
    + table_envs
    + figure_envs
    + reference_envs
    + caption_envs
    + algorithm_envs
    + list_envs
    + ["section", "subsection", "section*", "subsection*"]
    + ["abstract"]
    + ["bibliography"]
    + ["newcolumntype"] # corner case
)

texts = []


def find_env(wrapped_env: dict, query: List[str]) -> Union[str, None]:
    """
    Finds and returns the environment variable from the given query list that exists in the wrapped_env dictionary.

    Parameters:
        wrapped_env (dict): A dictionary containing environment variables as keys.
        query (list): A list of environment variables to search for.

    Returns:
        Union[str, None]: The environment variable found in the query list that exists in the wrapped_env dictionary,
                          or None if no matching environment variable is found.
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
    documentclass_index = -1
    for index, item in enumerate(data):
        if isinstance(item, dict) and "documentclass" in item:
            documentclass_index = index
            break

    if documentclass_index == -1:
        raise Exception("documentclass not found")

    # add usepackage in rendered document
    # notice: multiple inclusion will be ignored, so this addition is safe
    data.insert(documentclass_index + 1, "\n")  # for clarity
    data.insert(
        documentclass_index + 2, {"usepackage": "\\usepackage{" + package + "}"}
    )
    data.insert(documentclass_index + 3, "\n")  # for clarity


def enclose_abstract(data, title_color="red", text_color="green"):
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
    log.debug(f"main_content={main_content}")
    for index, item in enumerate(main_content):
        if isinstance(item, dict) and "abstract" in item:
            item["abstract"][CONTENT_INDEX] = {
                "textcolor": [
                    "\\textcolor{{{}}}{{".format(text_color),
                    *item["abstract"][CONTENT_INDEX],
                    "}\n",
                ]
            }

            log.debug(f"main_content={main_content}")
            break

    data[document_index + 3]["document"][1] = main_content


def add_color_definition(
    data, name2rgbcolor: Dict[str, Tuple[int, int, int]]
) -> Dict[str, str]:
    """
    Adds color definitions to the given data based on the
    provided name-to-RGB color mapping.

    Args:
        data: The data to modify, typically a list of dictionaries.
        name2rgbcolor (Dict[str, Tuple[int, int, int]]):
            A dictionary mapping color names to RGB values.

    Returns:
        Dict[str, str]: A dictionary mapping color names
            to the corresponding color definitions.

    Raises:
        Exception: If the 'documentclass' item is not found in the data.

    """

    # find the index of documentclass
    documentclass_index = -1
    for index, item in enumerate(data):
        if isinstance(item, dict) and "documentclass" in item:
            documentclass_index = index
            break

    if documentclass_index == -1:
        raise Exception("documentclass not found")

    add_usepackage_command(data, "xcolor")
    documentclass_index += 3

    name2color = {}
    for name, rgb_color in name2rgbcolor.items():
        color_name = name + "_color"
        data.insert(documentclass_index + 1, "\n")  # for clarity
        r, g, b = rgb_color
        data.insert(
            documentclass_index + 2,
            {"definecolor": f"\\definecolor{{{color_name}}}{{RGB}}{{{r}, {g}, {b}}}"},
        )
        data.insert(documentclass_index + 3, "\n")  # for clarity
        name2color[name] = color_name

    return name2color


def enclose_title(data, color="red") -> None:
    """
    Encloses the title of each dictionary item in the given data list with LaTeX formatting and a specified color.

    Parameters:
        data (list[dict]): A list of dictionaries containing the items to be modified.
        color (str): The color to use for the enclosed title. Defaults to 'red'.

    Returns:
        None

    Notes:
        - The function modifies the 'title' key in each dictionary item in the data list.
        - The function assumes that each dictionary item in the data list has a 'title' key.
        - The function uses LaTeX formatting to enclose the title text in the specified color.
            The format of the enclosed title is "\\title{{\\textcolor{{{}}}{{{}}}}}".format(color, title_text).
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


def enclose_section(data, color="red") -> None:
    """
    Encloses a section of data in curly braces with a specified color.

    Parameters:
        data (dict): The data to be enclosed.
        color (str, optional): The color of the enclosed section. Defaults to 'red'.

    Returns:
        dict: A dictionary representing the enclosed section.

    Raises:
        Exception: If a 'section' or 'subsection' key is not found in the data.
    """
    section_lists = ["section", "subsection", "section*", "subsection*"]
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, section_lists)
        if env is None:
            continue

        section_text = item[env][len(env) + 2 : -1]
        rendered_section = "\\{}{{\\textcolor{{{}}}{{{}}}}}".format(
            env, color, section_text
        )
        item[env] = rendered_section


def enclose_list(data, color="yellow") -> None:
    """
    Generate a brace group dictionary that encloses a list with a specified color.

    :param data: A dictionary containing either an 'itemize' or 'enumerate' key.
    :param color: The color to be applied to the enclosed list. Defaults to 'yellow'.
    :return: A brace group dictionary.
    :raises Exception: If 'itemize' or 'enumerate' key is not found in the data dictionary.
    """
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        env = find_env(item, list_envs)
        if env is None:
            continue

        data[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [{"color": ["\\color{{{}}}\n".format(color), *item[env], "\n"]}],
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
    log.debug(f"data={data}")
    for index, element in enumerate(data):
        if not isinstance(element, dict):
            continue

        log.debug(f"element={element}")

        if "caption" not in element:
            for key, value in element.items():
                if isinstance(value, list):
                    log.debug(f"value={value[CONTENT_INDEX]}")
                    enclose_caption_inside_env(value[CONTENT_INDEX], color)
            continue

        log.debug(f"element={element}")

        data[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [
                    "\n",
                    {"color": "\\color{{{}}}{{{}}}".format(color, element["caption"])},
                    "\n",
                ],
                {"end": "}"},
            ]
        }


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

        env = find_env(item, caption_envs)
        if env is None:
            continue

        log.debug(f"env={env}, item={item}")

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

        env = find_env(item, math_envs)

        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_equation(value[CONTENT_INDEX], color)
            continue
        
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
    for index, element in enumerate(data):
        if not isinstance(element, dict):
            continue

        if "tabular" not in element:
            for key, value in element.items():
                if isinstance(value, list):
                    enclose_tabular(value[CONTENT_INDEX], color)
            continue

        data[index] = {
            "BraceGroup": [
                {"begin": "{"},
                [
                    {
                        "color": [
                            "\\color{{{}}}\n".format(color),
                            *element["tabular"],
                            "\n",
                        ]
                    }
                ],
                {"end": "}"},
            ]
        }


def enclosed_table(data, color="cyan") -> None:
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, table_envs)
        if env is None:
            continue

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
        env = find_env(item, footnote_envs)
        if env is None:
            continue

        footenote_text = item[env][len(env) + 2 : -1]
        rendered_footnote = "\\{}{{\\color{{{}}}{{{}}}}}".format(
            env, color, footenote_text
        )
        item[env] = rendered_footnote


def enclose_text(data, color="olive"):
    result = []
    current_group = []

    for item in data:
        if isinstance(item, dict):
            # check if is an environment
            if find_env(item, non_text_envs) is not None:
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

        env = find_env(item, reference_envs)
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


def enclose_figure(data, color="black"):
    """
    Encloses a figure in an `mdframed` environment with a specified background color.

    Parameters:
        - data (list): A list of dictionaries representing figures.
        - color (str): The background color of the `mdframed` environment. Defaults to 'black'.

    Returns:
        None

    Note:
        This function requires `mdframed` to be installed.

    See:
        add_usepackage_command
    """
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, figure_envs)
        if env is None:
            continue

        for index, element in enumerate(item[env][CONTENT_INDEX]):
            if not isinstance(element, dict):
                continue

            if "includegraphics" not in element:
                continue

            item[env][CONTENT_INDEX][index] = {
                "mdframed": [
                    {"begin": "\\begin{{mdframed}}[backgroundcolor={}]".format(color)},
                    "\n",
                    [
                        item[env][CONTENT_INDEX][index],
                    ],
                    "\n",
                    {"end": "\\end{mdframed}"},
                ]
            }


def enclose_algorithm(data, color="pink"):
    for item in data:
        if not isinstance(item, dict):
            continue

        env = find_env(item, algorithm_envs)

        if env is None:
            for key, value in item.items():
                if isinstance(value, list):
                    enclose_algorithm(value[CONTENT_INDEX], color)
            continue

        item[env][1].insert(0, {"color": "\n\\color{{{}}}".format(color)})
