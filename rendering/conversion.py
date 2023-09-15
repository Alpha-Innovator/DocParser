from TexSoup.TexSoup import TexSoup
from TexSoup.TexSoup.data import TexEnv
from TexSoup.TexSoup.data import TexText
from TexSoup.TexSoup.data import TexCmd
from TexSoup.TexSoup.data import TexGroup


from logger import logger

log = logger.get_logger(__name__)


def to_list(tex_tree):
    str_tree = []
    for i in tex_tree:
        if isinstance(i, list):
            str_tree.append(i)
        elif isinstance(i, TexEnv):
            if i.args:
                for index, item in enumerate(i.all):
                    if isinstance(item, str) and item[0] == "\n":
                        break
                str_tree.append(
                    {
                        i.name: [
                            {"begin": i.begin + str(i.args)},
                            to_list(i.all[index:]),
                            {"end": i.end},
                        ]
                    }
                )
            else:
                str_tree.append(
                    {
                        i.name: [
                            {"begin": i.begin},
                            to_list(i.all),
                            {"end": i.end},
                        ]
                    }
                )
        elif isinstance(i, TexCmd):
            if i.name == "item":
                str_tree.append(
                    {
                        i.name: [
                            "\\" + i.name,
                            to_list(i.contents),
                        ]
                    }
                )
                continue
            str_tree.append({i.name: "\\" + i.name + str(i.args)})
        elif isinstance(i, TexText):
            str_tree.append(str(i.text))
        elif isinstance(i, TexGroup):
            str_tree.append(["{", to_list(TexSoup(i.value).expr.all), "}"])
        else:
            str_tree.append(str(i))

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
