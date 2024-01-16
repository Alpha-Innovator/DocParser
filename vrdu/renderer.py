from collections import defaultdict
import os
import shutil
from typing import List, Tuple, Union
import re


import vrdu.utils as utils
import vrdu.logger as logger
from vrdu.config import config, envs

from TexSoup.TexSoup import TexSoup
import TexSoup.app.conversion as conversion

log = logger.get_logger(__name__)


def find_env(wrapped_env: dict, query: List[str]) -> Union[str, None]:
    """
    Finds and returns the environment variable from the given query list
    that exists in the wrapped_env dictionary.

    Parameters:
        wrapped_env (dict): A dictionary containing environment variables as keys.
        query (list): A list of environment variables to search for.

    Returns:
        Union[str, None]: The environment variable found in the query list that exists in the wrapped_env dictionary, or None
        if no matching environment variable is found.
    """
    for env in query:
        if env in wrapped_env:
            return env

    return None


def is_text_eq(text: str):
    pattern = r"(\\\(.*?\\\))|(\$.*?\$)|(\\begin\{math\}.*?\\end\{math\})"
    matches = re.findall(pattern, text)

    for match in matches:
        if not re.search(r"\\\$", match[0]):
            return True

    return False


class Renderer:
    def __init__(self) -> None:
        self.texts = defaultdict(list)

    def render_section(self, data) -> None:
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
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.section_envs)
            if env is None:
                continue

            self.texts["Title"].append(item[env])
            item[env] = utils.colorize(item[env], "Title")

    def render_list(self, data: List) -> None:
        """
        Encloses dictionary items in a list with a brace group
        and modifies the data in-place.

        Args:
            data (List): The list of items to be processed.
            color (str, optional): The color to be applied to the enclosed items. Defaults to "yellow".

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
                    self.render_list(value[1])
                continue

            self.texts["List"].append(item[env])
            item[env] = utils.colorize(item[env], "List")

    def render_equation(self, data) -> None:
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
                    self.render_equation(value[1])
                continue

            self.texts["Equation"].append(item[env])
            item[env] = utils.colorize(item[env], "Equation")

    def render_text(self, data) -> None:
        for index, item in enumerate(data):
            if not isinstance(item, str):
                if not isinstance(item, dict):
                    continue
                for key, value in item.items():
                    if key.lower() not in envs.text_envs:
                        continue
                    if not isinstance(value, list):
                        continue
                    self.render_text(value[1])
                continue

            if not item or item == "\n" or item == "\n\n" or item.isspace():
                continue

            if is_text_eq(item):
                data[index] = utils.colorize(item, "Text-EQ")
                self.texts["Text-EQ"].append(item)
            else:
                data[index] = utils.colorize(item, "Text")
                self.texts["Text"].append(item)

            # format
            if item[0] == "\n":
                data[index] = "\n" + data[index]
            if item[-1] == "\n":
                data[index] += "\n"

    def add_color_definition(self, color_tex: str) -> None:
        """Adds color definitions to a LaTeX file.

        Args:
            color_tex (str): The path to the LaTeX file to modify.

        Raises:
            ValueError: If the beginning of the document is not found.

        Returns:
            None
        """
        with open(color_tex, "r") as f:
            content = f.read()

        definitions = ["\\usepackage{xcolor}"]
        for name, rgb_color in config.name2rgbcolor.items():
            color_name = config.name2color[name]
            r, g, b = rgb_color
            definition = f"\\definecolor{{{color_name}}}{{RGB}}{{{r}, {g}, {b}}}"
            definitions.append(definition)

        color_definitions = "\n" + "\n".join(definitions) + "\n"

        # Find location to insert package
        preamble = re.search(r"\\begin{document}", content)
        if not preamble:
            raise ValueError("begin of document not found")
        preamble_loc = preamble.start()

        # Insert package line
        content = (
            content[: preamble_loc] + color_definitions + content[preamble_loc:]
        )

        # Write updated content
        with open(color_tex, "w") as f:
            f.write(content)

    def add_layout_definition(self, color_tex: str) -> None:
        """Adds layout definitions to a LaTeX file.

        Args:
            color_tex (str): The path to the LaTeX file to modify.

        Raises:
            ValueError: If the end of the document is not found.

        Returns:
            None
        """
        with open(color_tex, "r") as f:
            content = f.read()

        # https://www.overleaf.com/learn/latex/Page_size_and_margins
        keys = config.layout_keys

        definitions = ["\\message{[vrdu_data_process: Info]}"]
        for key in keys:
            definition = f"\\message{{[vrdu_data_process: The {key} is: \\the\\{key}]}}"
            definitions.append(definition)

        layout_definitions = "\n" + "\n".join(definitions) + "\n"

        package_re = r"\\end{document}"
        match = re.search(package_re, content)
        if not match:
            raise ValueError("end of document not found")

        package_loc = match.start()

        # Insert package line
        content = content[:package_loc] + layout_definitions + content[package_loc:]

        # Write updated content
        with open(color_tex, "w") as f:
            f.write(content)

    def remove_hyperref_color(self, input_file):
        """
        Remove hyperref color from the input file.

        Parameters:
            input_file (str): The path to the input file.

        Raises:
            ValueError: If the `\\begin{document}` is not found in the input file.

        Returns:
            None

        Reference:
            https://www.overleaf.com/learn/latex/Hyperlinks
        """
        # Read the content of the input file
        with open(input_file, "r") as file:
            content = file.read()

        # Define the pattern to match the color definitions
        pattern = r"\\usepackage{hyperref}|\\usepackage(\[)?\[.*?\]?(\])?{hyperref}"

        preamble = re.search(r"\\begin{document}", content)
        if not preamble:
            raise ValueError("begin of document not found")
        preamble_loc = preamble.start()

        # forbidden the color used by hyperref
        hyper_setup = "\\hypersetup{colorlinks=false}\n"
        if re.search(pattern, content[:preamble_loc]):
            content = content[:preamble_loc] + hyper_setup + content[preamble_loc:]

        # Write the modified content back to the input file
        with open(input_file, "w") as file:
            file.write(content)

    def remove_lstlisting_color(self, input_file):
        # Read the content of the input file
        with open(input_file, "r") as file:
            content = file.read()

        pattern = r"\\lstset\{.*?\}"

        # Replace the color definitions with pure white
        modified_content = re.sub(pattern, "", content)

        # Write the modified content to the output file
        with open(input_file, "w") as file:
            file.write(modified_content)

    def modify_color_definitions(self, input_file, output_file):
        # Read the content of the input file
        with open(input_file, "r") as file:
            content = file.read()

        # Define the pattern to match the color definitions
        # FIXME: use defined color
        pattern = r"\\definecolor{([^}]+)}{RGB}{(\d+), (\d+), (\d+)}"

        # Replace the color definitions with pure white
        modified_content = re.sub(
            pattern, r"\\definecolor{\1}{RGB}{255, 255, 255}", content
        )

        # Write the modified content to the output file
        with open(output_file, "w") as file:
            file.write(modified_content)

    def get_env_orders(self, tex_file):
        with open(tex_file) as f:
            contents = f.read()
        colors = list(config.name2color.values())
        matches = []

        pattern = "|".join(rf"\b{re.escape(term)}\b" for term in colors)
        for m in re.finditer(pattern, contents):
            matches.append(m.group(0))

        # the definitions are discarded
        return matches[len(colors) :]

    def render_one_env(self, main_directory: str) -> None:
        """Render one environment by modifying the corresponding rendering color to black.

        Args:
            main_directory (str): The main directory.

        Returns:
            None: This function does not return anything.
        """
        color_tex_file = os.path.join(main_directory, "paper_colored.tex")
        white_tex_file = os.path.join(main_directory, "paper_white.tex")
        self.modify_color_definitions(color_tex_file, white_tex_file)
        env_orders = self.get_env_orders(white_tex_file)

        with open(white_tex_file, "r") as f:
            content = f.read()

        for index, env_color in enumerate(env_orders):
            # the first one is the color definition, skip it
            new_content = replace_nth(
                content, "{" + env_color + "}", r"{black}", index + 2
            )

            output_file = os.path.join(
                main_directory,
                "paper_" + config.folder_prefix + str(index).zfill(5) + ".tex",
            )
            with open(output_file, "w") as f:
                f.write(new_content)

    def render_caption(self, tex_file):
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\caption"
        matches = re.finditer(pattern, content)

        indexes = [(0, 0, "")]
        for match in matches:
            brackets = []
            start = match.start()
            end = match.end()
            complete = False
            while True:
                if content[end] == "{":
                    brackets.append("{")
                    complete = True
                elif content[end] == "}":
                    brackets.pop()
                if complete and len(brackets) == 0:
                    break
                end += 1

            end += 1
            caption = content[start:end]

            self.texts["Caption"].append(caption)
            colored_caption = utils.colorize(caption, "Caption")
            indexes.append((start, end, colored_caption))

        result = ""
        for i, _ in enumerate(indexes):
            if i == 0:
                continue
            result += content[indexes[i - 1][1] : indexes[i][0]]
            result += indexes[i][2]

        result += content[indexes[-1][1] :]

        with open(tex_file, "w") as f:
            f.write(result)

    def render_title(self, tex_file):
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\title"
        indexes = [(m.start(), m.end()) for m in re.finditer(pattern, content)]

        if len(indexes) > 1:
            raise ValueError("more than one title found")

        if len(indexes) == 0:
            log.debug("no title found")
            return

        brackets = []
        start, end = indexes[0]
        complete = False
        while True:
            if content[end] == "{":
                brackets.append("{")
                complete = True
            elif content[end] == "}":
                brackets.pop()
            if complete and len(brackets) == 0:
                break
            end += 1

        end += 1
        title = content[start:end]
        self.texts["PaperTitle"].append(title)
        colored_title = utils.colorize(title, "PaperTitle")
        content = content[:start] + colored_title + content[end:]

        with open(tex_file, "w") as f:
            f.write(content)

    def render_footnote(self, tex_file: str) -> None:
        """Renders footnotes in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering footnotes with a specified color.
        It searches for various footnote environments and applies colorization to their contents.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None
        """
        # \footnote{...}, \footnote[]{...}, \footnotetext{...}, \footnotetext[]{...}, \tablefootnote{}
        with open(tex_file) as f:
            content = f.read()

        for env_name in envs.footnote_envs:
            pattern = r"\\" + env_name + r"(?:\[[^\]]*\])?(?:\{[^}]*\})"
            matches = re.finditer(pattern, content)

            indexes = []
            indexes.append((0, 0, ""))

            for m in matches:
                start = m.start()
                end = m.end()

                # the regex is greedy, iterate to find the end of footnote env
                num_left_brackets = content[start:end].count("{")
                num_right_brackets = content[start:end].count("}")
                while num_right_brackets < num_left_brackets:
                    if content[end] == "{":
                        num_left_brackets += 1
                    elif content[end] == "}":
                        num_right_brackets += 1
                    end += 1

                footnote = content[start:end]
                colored_footnote = utils.colorize(footnote, "Footnote")
                indexes.append((start, end, colored_footnote))

            result = ""
            for i, _ in enumerate(indexes):
                if i == 0:
                    continue
                result += content[indexes[i - 1][1] : indexes[i][0]]
                result += indexes[i][2]

            result += content[indexes[-1][1] :]

            content = result

        with open(tex_file, "w") as f:
            f.write(content)

    def render_abstract(self, tex_file):
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\begin{abstract}.*?\\end{abstract}"
        indexes = [
            (m.start(), m.end()) for m in re.finditer(pattern, content, re.DOTALL)
        ]

        if len(indexes) > 1:
            raise ValueError("more than one title found")
        if not indexes:
            log.debug("no abstract found")
            return

        start, end = indexes[0]
        abstract = content[start:end]
        self.texts["Abstract"].append(abstract)
        colored_abstract = utils.colorize(abstract, "Abstract")
        result = content[:start] + colored_abstract + content[end:]

        with open(tex_file, "w") as f:
            f.write(result)

    def render_tabular(self, tex_file: str) -> None:
        """Renders tabular environments in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering tabular environments with a specified color.
        It searches for tabular environments in the file and applies colorization to their contents.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None
        """
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\begin{tabular}.*?\\end{tabular}"
        indexes = [
            (m.start(), m.end()) for m in re.finditer(pattern, content, re.DOTALL)
        ]

        if not indexes:
            return

        result = content[: indexes[0][0]]
        for i, _ in enumerate(indexes):
            if i > 0:
                result += content[indexes[i - 1][1] : indexes[i][0]]
            tabular = content[indexes[i][0] : indexes[i][1]]
            # ignore the case where tabular is used to arange figures
            if "includegraphics" in tabular:
                result += tabular
                continue
            self.texts["Table"].append(tabular)
            colored_tabular = utils.colorize(tabular, "Table")
            result += colored_tabular

        result += content[indexes[-1][1] :]

        with open(tex_file, "w") as f:
            f.write(result)

    def render_algorithm(self, tex_file):
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\begin{algorithm[*]?}(.*?)\\end{algorithm[*]?}"
        indexes = [
            (m.start(), m.end()) for m in re.finditer(pattern, content, re.DOTALL)
        ]

        if not indexes:
            return

        result = content[: indexes[0][0]]
        for i, _ in enumerate(indexes):
            if i > 0:
                result += content[indexes[i - 1][1] : indexes[i][0]]
            algorithm = content[indexes[i][0] : indexes[i][1]]
            self.texts["Algorithm"].append(algorithm)
            colored_algorithm = utils.colorize(algorithm, "Algorithm")
            result += colored_algorithm

        result += content[indexes[-1][1] :]

        with open(tex_file, "w") as f:
            f.write(result)

    def extract_graphics(self, tex_file):
        with open(tex_file, "r") as file:
            content = file.read()

        pattern = r"\\includegraphics(?:\[(.*?)\])?{(.*?)}"
        matches = re.findall(pattern, content)
        for match in matches:
            graphic = "\\includegraphics"
            if match[0]:
                graphic += f"[{match[0]}]"
            graphic += f"{{{match[1]}}}"
            self.texts["Figure"].append(graphic)

    def render_code(self, tex_file):
        with open(tex_file, "r") as file:
            content = file.read()
        # pattern 1: code environment
        # pattern 2: lstinputlisting to input a file
        pattern = (
            r"\\begin{(verbatim|lstlisting|program)[*]?}(.*?)\\end{\1[*]?}"
            + "|"
            + r"\\lstinputlisting\[[^\]]*\]{[^\}]*}"
        )
        indexes = [
            (m.start(), m.end()) for m in re.finditer(pattern, content, re.DOTALL)
        ]

        if not indexes:
            return

        result = content[: indexes[0][0]]
        for i, _ in enumerate(indexes):
            if i > 0:
                result += content[indexes[i - 1][1] : indexes[i][0]]
            code = content[indexes[i][0] : indexes[i][1]]
            self.texts["Code"].append(code)
            colored_code = utils.colorize(code, "Code")
            result += colored_code

        result += content[indexes[-1][1] :]

        content = result

        with open(tex_file, "w") as f:
            f.write(result)

    def render_float_envs(self, tex_file):
        self.render_caption(tex_file)
        self.render_footnote(tex_file)
        # self.extract_graphics(tex_file)
        self.render_algorithm(tex_file)
        self.render_tabular(tex_file)
        self.render_code(tex_file)
        # the following two envs are placed here because they use string regex to render
        self.render_title(tex_file)
        self.render_abstract(tex_file)

    def render_simple_envs(self, tex_file):
        data, start, end = utils.data_from_tex_file(tex_file)
        # Save the raw parsed data for debugging purposes
        raw_data_file = os.path.join(
            os.path.dirname(tex_file), "output/result/raw_parsed_data.json"
        )
        utils.export_to_json(data, raw_data_file)

        self.render_section(data)
        self.render_list(data)
        self.render_equation(data)
        self.render_text(data)
        # self.enclose_reference(data, color=name2color["Reference"])

        # Write the modified data back to the TeX file
        utils.tex_file_from_data(data, tex_file, start=start, end=end)

    def render_all_env(self, tex_file):
        self.render_simple_envs(tex_file)
        self.render_float_envs(tex_file)

    def render(self, origin_tex_file):
        original_dir = os.path.dirname(origin_tex_file)

        color_tex_file = os.path.join(original_dir, "paper_colored.tex")
        shutil.copyfile(origin_tex_file, color_tex_file)

        self.add_color_definition(color_tex_file)
        self.add_layout_definition(color_tex_file)
        self.remove_hyperref_color(color_tex_file)
        self.remove_lstlisting_color(color_tex_file)

        self.render_all_env(color_tex_file)

        # change the enclose color of semantic elements one by one and generate corresponding tex files
        self.render_one_env(original_dir)

        text_file = os.path.join(original_dir, "output/result/texts.json")
        utils.export_to_json(self.texts, text_file)


def extract_main_content(tex_file: str) -> Tuple[str, int, int]:
    """Extracts the main content from a LaTeX file.

    Args:
        tex_file (str): The path to the LaTeX file.

    Returns:
        Tuple[str, int, int]: A tuple containing the main content of the LaTeX file,
            the start position of the main content in the file, and the end position
            of the main content in the file.
    """
    with open(tex_file) as f:
        content = f.read()

    start = content.find("\\begin{document}")
    end = content.find("\\end{document}")

    if start == -1 or end == -1:
        raise ValueError("Document tags not found")

    start += len("\\begin{document}")
    main_content = content[start:end]

    return main_content, start, end


def data_from_tex_file(tex_file: str) -> Tuple[List[Union[dict, str]], int, int]:
    """Extracts data from a Tex file using TexSoup.

    Args:
        tex_file (str): The path to the Tex file.

    Returns:
        Tuple[List, int, int]: A tuple containing the extracted data, the start
        position of the extracted content, and the end position of the extracted
        content.
    """
    main_content, start, end = extract_main_content(tex_file)
    tex_tree = TexSoup(main_content).expr.all
    data = conversion.to_list(tex_tree)

    return data, start, end


def tex_file_from_data(
    data: List[Union[dict, str]],
    tex_file: str,
    start: int = 0,
    end: int = -1,
) -> None:
    """Generate a TeX file from the given TexSoup data.

    Args:
        data (List[Union[dict, str]]): The data to be converted into LaTeX.
        tex_file (str): The path of the TeX file to be generated.
        start (int, optional): The starting position in the TeX file to replace content. Defaults to 0.
        end (int, optional): The ending position in the TeX file to replace content. Defaults to -1.

    Returns:
        None: This function does not return any value.
    """
    with open(tex_file, "r") as f:
        content = f.read()

    # convert the data into latex
    rendered_tex = conversion.to_latex(data)

    content = content[:start] + rendered_tex + content[end:]

    with open(tex_file, "w") as f:
        f.write(content)
