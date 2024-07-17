import re

from DocParser.TexSoup.TexSoup import TexSoup
from DocParser.TexSoup.TexSoup.data import TexEnv, TexText, TexCmd, TexGroup


from DocParser.vrdu import logger
from DocParser.vrdu.config import envs

log = logger.get_logger(__name__)


def remove_outer_curly_brackets(text):
    pattern = r"^\{(.*)\}$"
    match = re.match(pattern, text)
    if match:
        return match.group(1)
    else:
        return text


def split_on_double_newline(text):
    if text == "\n\n":
        return [text]

    # https://www.overleaf.com/learn/latex/Paragraphs_and_new_lines
    modified_text = text.replace(r"(\\par)", r"\n\n")
    result = re.split(r"(\n\n)", modified_text)
    return result


def to_list(tex_tree):
    # TODO: simplify code logic, especially for text envs
    str_tree = []
    for i in tex_tree:
        if isinstance(i, list):
            str_tree.append(i)
        elif isinstance(i, TexEnv):
            if i.name in envs.inline_math_envs:  # inline math mode
                str_tree.append(str(i))
            elif (
                i.name
                in envs.math_envs
                + envs.algorithm_envs
                + envs.tabular_envs
                + envs.list_envs
                + envs.nonexpand_envs
            ):
                str_tree.append({i.name: str(i)})
            elif (
                str_tree and isinstance(str_tree[-1], str) and str_tree[-1][-1] != "\n"
            ):
                str_tree.append(str_tree.pop() + str(i))
            else:
                argc = sum(len(arg.all) for arg in i.args)
                str_tree.append(
                    {
                        i.name: [
                            {"begin": i.begin + str(i.args)},
                            to_list(i.all[argc:]),
                            {"end": i.end},
                        ]
                    }
                )
        elif isinstance(i, TexCmd):
            if i.name == "item":
                str_tree.append(str(i))
            elif i.name == "def":
                macro_name = remove_outer_curly_brackets(str(i.args[0]))
                parameter_text = i.args[1].string
                str_tree.append({i.name: "\\" + i.name + macro_name + parameter_text})
            elif i.name == "label":
                str_tree.append({i.name: "\\" + i.name + str(i.args)})
            elif i.name in envs.ignore_envs:
                str_tree.append(str(i))
            # if this cmd is an inline command, ignore it
            # https://en.wikibooks.org/wiki/LaTeX/Special_Characters
            elif (
                str_tree and isinstance(str_tree[-1], str) and str_tree[-1][-1] != "\n"
            ):
                str_tree.append(str_tree.pop() + str(i))
            else:
                str_tree.append({i.name: "\\" + i.name + str(i.args)})
        elif isinstance(i, TexText):
            str_tree.append(str(i.text))
        elif isinstance(i, TexGroup):
            str_tree.append(["{", to_list(TexSoup(i.value).expr.all), "}"])
        else:
            str_tree.append(str(i))

        # merge texts
        if (
            len(str_tree) >= 2
            and isinstance(str_tree[-1], str)
            and isinstance(str_tree[-2], str)
        ):
            cur = str_tree.pop()
            str_tree[-1] += cur

        # split texts into paragraphs with '\n\n'
        if isinstance(str_tree[-1], str):
            result = split_on_double_newline(str_tree[-1])
            str_tree.pop()
            str_tree.extend([r for r in result if r])

    return str_tree


def to_latex(tex_json):
    """
    Converts a JSON-like structure into LaTeX code.

    Parameters:
    tex_json (dict or list or str): The JSON-like structure to convert.

    Returns:
    str: The LaTeX code generated from the input structure.
    """
    if isinstance(tex_json, dict):
        tex_code = "".join([to_latex(val) for val in tex_json.values()])
    elif isinstance(tex_json, list):
        tex_code = "".join([to_latex(val) for val in tex_json])
    else:
        tex_code = tex_json

    return tex_code
