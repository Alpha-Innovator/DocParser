from collections import defaultdict
import os
import shutil
from typing import List, Union
import re


from TexSoup.app import conversion
from TexSoup.TexSoup import TexSoup
from TexSoup.TexSoup.data import TexEnv


import vrdu.utils as utils
import vrdu.logger as logger
from vrdu.config import config, envs

log = logger.get_logger(__name__)


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


class Renderer:
    def __init__(self) -> None:
        self.texts = defaultdict(list)

    def enclose_title(self, data, color="red") -> None:
        # TODO: add title rendering
        pass

    def enclose_section(self, data, color="red") -> None:
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

            self.texts["Title"].append(item[env])
            title_text = item[env][len(env) + 2 : -1]
            item[env] = (
                "\\" + env + "{" + r"\textcolor{" + color + "}{" + title_text + "}}"
            )

    def enclose_list(self, data: List, color: str = "yellow") -> None:
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
                    self.enclose_list(value[1], color)
                continue

            self.texts["List"].append(item[env])
            item[env] = r"{\color{" + color + "}{" + item[env] + "}}"

    def enclose_caption(self, data, color="orange") -> None:
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
                    self.enclose_caption(value[1], color)
                continue

            self.texts["Caption"].append(item[env])
            item[env] = r"\color{" + color + "}{" + item[env] + "}"

    def enclose_equation(self, data, color="green") -> None:
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
                    self.enclose_equation(value[1], color)
                continue

            self.texts["Equation"].append(item[env])
            item[env] = r"{\color{" + color + "}{" + item[env] + "}}"

    def enclose_tabular(self, data: List, color="cyan"):
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
                        self.enclose_tabular(value[1], color)
                continue

            self.texts["Table"].append(item[env])
            item[env] = r"{\color{" + color + "}{" + item[env] + "}}"

    def enclose_footnote(self, data, color="red") -> None:
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
                    self.enclose_footnote(value[1], color)
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

                self.texts["Footnote"].append(str(element))
                color_footnote = r"\color{" + color + "}" + footnote

                if len(element.args) > 1:
                    element.args[1].string = color_footnote
                else:
                    element.args[0].string = color_footnote

            data[index] = conversion.to_latex(conversion.to_list(parsed))

    def enclose_text(self, data, text_color="olive", text_eq_color="green") -> None:
        for index, item in enumerate(data):
            if not isinstance(item, str):
                if not isinstance(item, dict):
                    continue
                for key, value in item.items():
                    if key.lower() not in envs.text_envs:
                        continue
                    if not isinstance(value, list):
                        continue
                    self.enclose_text(value[1], text_color, text_eq_color)
                continue

            if not item or item == "\n" or item == "\n\n" or item.isspace():
                continue

            if is_text_eq(item):
                data[index] = r"\textcolor{" + text_eq_color + "}{" + item + "}"
                self.texts["Text-EQ"].append(item)
            else:
                data[index] = "\\textcolor{" + text_color + "}{" + item + "}"
                self.texts["Text"].append(item)

            # format
            if item[0] == "\n":
                data[index] = "\n" + data[index]
            if item[-1] == "\n":
                data[index] += "\n"

    def enclose_reference(self, data, color="violet") -> None:
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.reference_envs)
            if env is None:
                continue

            item[env] = r"{\color{" + color + "}\n" + item[env] + "}"

    def extract_figures(self, data):
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.graphic_envs)
            if env is None:
                for key, value in item.items():
                    if not isinstance(value, list):
                        continue
                    self.extract_figures(value[1])
                continue

            self.texts["Figure"].append(item[env])

    def enclose_algorithm(self, data, color="pink"):
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
                    self.enclose_algorithm(value[1], color)
                continue

            self.texts["Algorithm"].append(item[env])
            item[env] = r"{\color{" + color + "}" + item[env] + "}"

    def enclose_code(self, data, color="blue"):
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.code_envs)

            if env is None:
                for key, value in item.items():
                    if not isinstance(value, list):
                        continue
                    self.enclose_code(value[1], color)
                continue

            self.texts["Code"].append(item[env])
            item[env] = r"{\color{" + color + "}" + item[env] + "}"

    def add_color_definition(self, latex_file):
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

    def add_layout_definition(self, latex_file: str):
        keys = [
            "columnwidth",
            "columnsep",
            "textwidth",
            "paperwidth",
            "hoffset",
            "oddsidemargin",
        ]

        definitions = []
        for key in keys:
            definition = (
                "\\message{{[vrdu_data_process: The {0} is: \\the\\{0}]}}".format(key)
            )
            definitions.append(definition)

        layout_definitions = "\n".join(definitions) + "\n"

        with open(latex_file, "r") as f:
            content = f.read()
        package_re = r"\\end{document}"
        match = re.search(package_re, content)
        if not match:
            raise ValueError("end of document not found")

        package_loc = match.start()

        # Insert package line
        content = (
            content[: package_loc - 1] + layout_definitions + content[package_loc:]
        )

        # Write updated content
        with open(latex_file, "w") as f:
            f.write(content)

    def modify_color_definitions(self, input_file, output_file):
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

    def render_all_env(self, data):
        name2color = config.name2color
        self.enclose_section(data, color=name2color["Title"])

        self.enclose_list(data, color=name2color["List"])

        self.enclose_caption(data, color=name2color["Caption"])

        self.enclose_equation(data, color=name2color["Equation"])

        self.enclose_tabular(data, color=name2color["Table"])

        self.enclose_footnote(data, color=name2color["Footnote"])

        self.enclose_reference(data, color=name2color["Reference"])

        self.enclose_algorithm(data, color=name2color["Algorithm"])

        self.extract_figures(data)

        # enclose_code(data, color=name2color["Code"])

        self.enclose_text(
            data,
            text_color=name2color["Text"],
            text_eq_color=name2color["Text-EQ"],
        )

    def render_one_env(self, original_dir):
        color_tex_file = os.path.join(original_dir, "paper_colored.tex")
        white_tex_file = os.path.join(original_dir, "paper_white.tex")
        self.modify_color_definitions(color_tex_file, white_tex_file)
        path = os.path.dirname(white_tex_file)
        for env in envs.complex_env_list:
            num_items = len(self.texts[env])
            for i in range(num_items):
                output_file = os.path.join(path, f"paper_{env}_{i}.tex")
                shutil.copyfile(white_tex_file, output_file)

                with open(output_file, "r") as f:
                    content = f.read()

                # the first one is the color definition, skip it
                new_content = utils.replace_nth(content, env + "_color", "black", i + 2)

                with open(output_file, "w") as f:
                    f.write(new_content)

    def render(self, origin_tex_file):
        original_dir = os.path.dirname(origin_tex_file)

        color_tex_file = os.path.join(original_dir, "paper_colored.tex")
        shutil.copyfile(origin_tex_file, color_tex_file)

        self.add_color_definition(color_tex_file)
        self.add_layout_definition(color_tex_file)

        # use colors to enclose all semantic elements
        data, start, end = utils.data_from_tex_file(color_tex_file)

        # Save the raw parsed data for debugging purposes
        raw_data_file = os.path.join(original_dir, "output/result/raw_parsed_data.json")
        utils.export_to_json(data, raw_data_file)

        self.render_all_env(data)
        utils.tex_file_from_data(data, color_tex_file, start=start, end=end)

        # change the enclose color of semantic elements one by one and generate corresponding tex files
        self.render_one_env(original_dir)

        text_file = os.path.join(original_dir, "output/result/texts.json")
        utils.export_to_json(self.texts, text_file)
