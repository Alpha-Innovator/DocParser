import json
import os
from typing import Any

from TexSoup.TexSoup import TexSoup
import rendering.conversion as conversion


def export_to_json(data, file_path) -> None:
    """
    Write the contents of a dictionary to a JSON file.

    Parameters:
        data (dict): The dictionary to be written to the file.
        file_path (str): The path to the JSON file.
    """
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file)


def load_json(file_path) -> Any:
    """
    Load a JSON file into a dictionary.

    Parameters:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data as a dictionary.
    """
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
    return data


def get_main_content(data):
    """
    Generate the main content of a document.

    Parameters:
    - data (list): A list of dictionaries representing the document.

    Returns:
    - main_content (str): The main content of the document.

    Raises:
    - Exception: If the document is not found in the data.

    """
    main_content = None
    for item in data:
        if isinstance(item, dict) and 'document' in item:
            # first element and last element are \begin{document} and \end{document}
            main_content = item['document'][1]
            break

    if main_content is None:
        raise Exception("document not found")

    return main_content


def data_from_tex_file(tex_file, debug_mode: bool = False) -> list:
    """
    Reads a given tex file and extracts data from it.

    Args:
        tex_file (str): The path to the tex file.
        debug_mode (bool, optional): If True, enables debug mode. Defaults to False.

    Returns:
        list: The extracted data from the tex file.
    """
    tex_text = open(tex_file).read()
    tex_tree = TexSoup(tex_text).expr.all
    data = conversion.to_list(tex_tree)

    if debug_mode:
        base_name = os.path.basename(tex_file)
        json_file = base_name + ".json"
        export_to_json(data, json_file)

    return data


def tex_file_from_data(data: list, tex_file: str, debug_mode: bool = False) -> None:
    """
    Generate a TeX file from a dictionary/list of data.

    Args:
        data (list): The data to be converted into a TeX file.
        tex_file (str): The path to the output TeX file.
        debug_mode (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        None: This function does not return anything.
    """
    if debug_mode:
        base_name = os.path.basename(tex_file)
        json_file = base_name + ".json"
        export_to_json(data, json_file)

    # convert the data into latex
    rendered_tex = conversion.to_latex(data)

    with open(tex_file, 'w') as f:
        f.write(rendered_tex)
