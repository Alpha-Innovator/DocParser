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


class Renderer:
    def __init__(self) -> None:
        self.texts = defaultdict(list)

    def render(self, origin_tex: str) -> None:
        """Render the colored version of a LaTeX document.

        This method performs the rendering process for generating the colored version of a LaTeX document.
        It includes the following steps:
        1. Create a copy of the original LaTeX file with a new name.
        2. Add color definitions and layout definitions to the copied file.
        3. Remove color definitions that may cause conflicts.
        4. Render all environments in the copied file.
        5. Iterate over semantic elements and change their enclosing color, generating corresponding LaTeX files.
        6. Export the rendered texts to a JSON file.

        Args:
            origin_tex (str): The path to the original LaTeX file.

        Returns:
            None

        Examples:
            >>> renderer = LaTeXRenderer()
            >>> renderer.render("original.tex")
        """
        main_directory = os.path.dirname(origin_tex)

        # copy the original tex file
        color_tex = os.path.join(main_directory, "paper_colored.tex")
        shutil.copyfile(origin_tex, color_tex)

        self.add_color_definition(color_tex)
        self.add_layout_definition(color_tex)

        # remove color definitions to prevent conflict
        self.remove_hyperref_color(color_tex)
        self.remove_lstlisting_color(color_tex)

        self.render_all_env(color_tex)

        # change the enclose color of semantic elements one by one and generate corresponding tex files
        self.render_one_env(main_directory)

        text_file = os.path.join(main_directory, "output/result/texts.json")
        utils.export_to_json(self.texts, text_file)

    def render_all_env(self, color_tex: str) -> None:
        """
        Render all environments, it includes simple environments and float environments.

        Args:
            color_tex (str): The color texture.

        Returns:
            None
        """
        self.render_simple_envs(color_tex)
        self.render_float_envs(color_tex)

    def render_simple_envs(self, color_tex: str) -> None:
        """Renders simple environments in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering various simple environments,
        such as sections, lists, equations, and text.
        The modifications are done in-place, directly modifying the provided file.

        Args:
            color_tex (str): The path to the LaTeX file to modify.

        Returns:
            None

        Raises:
            EOFError: If TexSoup failed to parse the input file due to runaway environments.
            AssertionError: If TexSoup failed to parse the input file due to Command \\item invalid in math mode.

        """
        data, start, end = data_from_tex_file(color_tex)

        self.render_section(data)
        self.render_list(data)
        self.render_equation(data)
        self.render_text(data)
        # self.enclose_reference(data, color=name2color["Reference"])

        # Write the modified data back to the TeX file
        tex_file_from_data(data, color_tex, start=start, end=end)

    def render_float_envs(self, tex_file: str) -> None:
        """Renders float environments in a LaTeX file.

        This method applies rendering to various float environments in the LaTeX file
        by calling specific rendering methods for each type of environment.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None
        """

        # Step 1: Render captions
        self.render_caption(tex_file)

        # Step 2: Render footnotes
        self.render_footnote(tex_file)

        # Step 3: Extract graphics paths
        self.extract_graphics(tex_file)

        # Step 4: Render algorithm environments
        self.render_algorithm(tex_file)

        # Step 5: Render tabular environments
        self.render_tabular(tex_file)

        # Step 6: Render code environments
        self.render_code(tex_file)

        # the following two envs are placed here because they also use string regex to render
        # Step 7: Render titles
        self.render_title(tex_file)

        # Step 8: Render abstracts
        self.render_abstract(tex_file)

    def render_section(self, data: List[Union[dict, str]]) -> None:
        """Render sections in the given data with a configured color.
        This function modifies the data in-place.

        Args:
            data (List[Union[dict, str]]): The data to be enclosed.
            color (str, optional): The color of the enclosed section. Defaults to 'red'.

        Returns:
            None
        """
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.section_envs)
            if env is None:
                continue

            self.texts["Title"].append(item[env])
            item[env] = utils.colorize(item[env], "Title")

    def render_list(self, data: List[Union[dict, str]]) -> None:
        """Render equations in the given data with a configured color.
        This function modifies the data in-place.

        Args:
            data (List[Union[dict, str]]): The list of items to be processed.

        Returns:
            None
        """
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.list_envs)
            if env is None:
                for value in item.values():
                    if not isinstance(value, list):
                        continue
                    self.render_list(value[1])
                continue

            self.texts["List"].append(item[env])
            item[env] = utils.colorize(item[env], "List")

    def render_equation(self, data: List[Union[dict, str]]) -> None:
        """Render equations in the given data with a configured color.

        Args:
            - data (List[Union[dict, str]]): The data containing equations to enclose.

        Returns:
            None
        """
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.math_envs)

            if env is None:
                for value in item.values():
                    if not isinstance(value, list):
                        continue
                    self.render_equation(value[1])
                continue

            self.texts["Equation"].append(item[env])
            item[env] = utils.colorize(item[env], "Equation")

    def render_text(self, data: List[Union[dict, str]]) -> None:
        """Render texts and text-eqs in the given data with a configured color.
        This function modifies the data in-place.

        Args:
            data (List[Union[dict, str]]): The list of items to be processed.

        Returns:
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
        content = content[:preamble_loc] + color_definitions + content[preamble_loc:]

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

        Reference:
            https://www.overleaf.com/learn/latex/Page_size_and_margins
        """
        with open(color_tex, "r") as f:
            content = f.read()

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

    def remove_hyperref_color(self, color_tex: str) -> None:
        """Removes hyperref color settings from a LaTeX file.

        Args:
            color_tex (str): The path to the LaTeX file to modify.

        Raises:
            ValueError: If the beginning of the document is not found.

        Returns:
            None

        Reference:
            https://www.overleaf.com/learn/latex/Hyperlinks
        """
        # Read the content of the input file
        with open(color_tex, "r") as file:
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
        with open(color_tex, "w") as file:
            file.write(content)

    def remove_lstlisting_color(self, color_tex: str) -> None:
        """Remove color definitions from a LaTeX file.

        Args:
            color_tex (str): The path to the LaTeX file.

        Returns:
            None
        """
        # Read the content of the input file
        with open(color_tex, "r") as file:
            content = file.read()

        # delete the color definitions
        pattern = r"\\lstset\{.*?\}"
        modified_content = re.sub(pattern, "", content)

        # Write the modified content to the output file
        with open(color_tex, "w") as file:
            file.write(modified_content)

    def modify_color_definitions(self, input_file: str, output_file: str) -> None:
        """Modify the pre-defined color definitions in the input file and write the modified content to the output file.

        Args:
            input_file (str): The path to the input file.
            output_file (str): The path to the output file.

        Returns:
            None
        """
        with open(input_file, "r") as file:
            content = file.read()

        # Define the pattern to match the color definitions
        for name in config.name2rgbcolor.keys():
            color_name = config.name2color[name]
            pattern = r"\\definecolor{" + color_name + r"}{RGB}{(\d+), (\d+), (\d+)}"

            # Replace the color definitions with pure white
            content = re.sub(
                pattern,
                r"\\definecolor{" + color_name + r"}{RGB}{255, 255, 255}",
                content,
            )

        with open(output_file, "w") as file:
            file.write(content)

    def get_env_orders(self, tex_file: str) -> List[str]:
        """Returns a list of environment orders based on the contents of the given `tex_file`.

        Args:
            tex_file (str): The path to the .tex file.

        Returns:
            List[str]: A list of environment orders.
        """
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
        ordered_env_colors = self.get_env_orders(white_tex_file)
        suffix = "_color"
        index_map = defaultdict(int)

        with open(white_tex_file, "r") as f:
            content = f.read()

        for index, env_color in enumerate(ordered_env_colors):
            env = env_color[: -len(suffix)]
            # the first one is the color definition, skip it
            new_content = replace_nth(
                content, "{" + env_color + "}", r"{black}", index_map[env] + 2
            )

            output_file = os.path.join(
                main_directory,
                f"paper_{config.folder_prefix}_{str(index).zfill(5)}_{env}_{str(index_map[env]).zfill(5)}.tex",
            )
            index_map[env] += 1
            with open(output_file, "w") as f:
                f.write(new_content)

    def render_caption(self, tex_file: str) -> None:
        """Renders captions in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering captions with a specified color.
        It searches for caption commands in the file and applies colorization to their contents.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None
        """
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\caption(?:\[[^\]]*\])?(?:\{[^}]*\})"
        result = self._render_simple_envs(content, pattern, "Caption")

        with open(tex_file, "w") as f:
            f.write(result)

    def render_title(self, tex_file: str) -> None:
        """Renders the title in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering the title with a specified color.
        It searches for the title command in the file and applies colorization to its content.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None
        """
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\title(?:\{[^}]*\})"
        result = self._render_simple_envs(content, pattern, "PaperTitle")

        with open(tex_file, "w") as f:
            f.write(result)

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

            content = self._render_simple_envs(content, pattern, "Footnote")

        with open(tex_file, "w") as f:
            f.write(content)

    def _render_simple_envs(self, content: str, pattern: str, category: str) -> str:
        """Renders specific environments in the content using replacement.

        This method searches for occurrences of a pattern in the content and replaces them with colored versions.
        The replacement is based on the specified category for colorization.

        Args:
            content (str): The content of the LaTeX file.
            pattern (str): The regular expression pattern to match.
            category (str): The category of the environment for colorization.

        Returns:
            str: The modified content with the rendered environments.
        """
        matches = re.finditer(pattern, content)
        result = ""
        index = 0
        for match in matches:
            start = match.start()
            end = match.end()

            # the regex is greedy, iterate to find the end of footnote env
            num_left_brackets = content[start:end].count("{")
            num_right_brackets = content[start:end].count("}")
            while num_right_brackets < num_left_brackets:
                if content[end] == "{":
                    num_left_brackets += 1
                elif content[end] == "}":
                    num_right_brackets += 1
                end += 1

            category_content = content[start:end]

            self.texts[category].append(category_content)
            colored_title = utils.colorize(category_content, category)
            result += content[index:start]
            result += colored_title
            index = end

        result += content[index:]
        return result

    def render_abstract(self, tex_file: str) -> None:
        """Renders the abstract section in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering the abstract section with a specified color.
        It searches for the abstract section in the file and applies colorization to its contents.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None

        Raises:
            ValueError: If more than one abstract section is found.
        """
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\begin{abstract}.*?\\end{abstract}"
        indexes = [
            (m.start(), m.end()) for m in re.finditer(pattern, content, re.DOTALL)
        ]

        if len(indexes) > 1:
            raise ValueError("more than one abstract found")

        if not indexes:
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
        pattern = "|".join(
            [
                r"\\begin{0}.*?\\end{0}".format(tabular_env)
                for tabular_env in envs.tabular_envs
            ]
        )
        result = self._render_float_envs(content, pattern, "Table")

        with open(tex_file, "w") as f:
            f.write(result)

    def render_algorithm(self, tex_file: str) -> None:
        """Renders algorithm environments in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering algorithm environments with a specified color.
        It searches for algorithm environments in the file and applies colorization to their contents.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None
        """
        with open(tex_file) as f:
            content = f.read()

        pattern = r"\\begin{algorithm[*]?}(.*?)\\end{algorithm[*]?}"
        result = self._render_float_envs(content, pattern, "Algorithm")

        with open(tex_file, "w") as f:
            f.write(result)

    def render_code(self, tex_file: str) -> None:
        """Renders code environments in a LaTeX file.

        This method modifies the content of a LaTeX file by rendering code environments with a specified color.
        It searches for code environments and `\\lstinputlisting` commands in the file and applies colorization to their contents.

        Args:
            tex_file (str): The path to the LaTeX file to modify.

        Returns:
            None

        Notes:
            There are two types of code environments:
            - pattern 1: code environment
            - pattern 2: lstinputlisting to input a file

        Reference:
            https://en.wikibooks.org/wiki/LaTeX/Source_Code_Listings
        """
        with open(tex_file, "r") as file:
            content = file.read()

        pattern = (
            r"\\begin{(verbatim|lstlisting|program)[*]?}(.*?)\\end{\1[*]?}"
            + "|"
            + r"\\lstinputlisting\[[^\]]*\]{[^\}]*}"
        )
        result = self._render_float_envs(content, pattern, "Code")

        with open(tex_file, "w") as f:
            f.write(result)

    def _render_float_envs(self, content: str, pattern: str, category: str) -> str:
        """Renders specific float environments in the content.

        This method searches for occurrences of a pattern in the content and replaces them with colored versions.
        The replacement is based on the specified category for colorization.

        Args:
            content (str): The content of the LaTeX file.
            pattern (str): The regular expression pattern to match.
            category (str): The category of the environment for colorization.

        Returns:
            str: The modified content with the rendered float environments.
        """
        indexes = [
            (m.start(), m.end()) for m in re.finditer(pattern, content, re.DOTALL)
        ]

        if not indexes:
            log.debug(f"no {category} found")
            return content

        result = content[: indexes[0][0]]
        for i, _ in enumerate(indexes):
            if i > 0:
                result += content[indexes[i - 1][1] : indexes[i][0]]
            float_env = content[indexes[i][0] : indexes[i][1]]

            # filter tablle of figures
            if category == "Table" and float_env.find("\\includegraphics") != -1:
                continue

            # TODO: filter table in equation envs

            self.texts[category].append(float_env)
            colored_float_env = utils.colorize(float_env, category)
            result += colored_float_env

        result += content[indexes[-1][1] :]
        return result

    def extract_graphics(self, tex_file: str) -> None:
        """Extracts graphics paths from a LaTeX file.

        This method reads a LaTeX file and extracts the paths of graphics included using the `\\includegraphics` command.
        The extracted graphics paths are stored in the `texts["Figure"]` list.

        Args:
            tex_file (str): The path to the LaTeX file to extract graphics from.

        Returns:
            None
        """
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


def find_env(wrapped_env: dict, query: List[str]) -> Union[str, None]:
    """
    Finds and returns the environment variable from the given query list
    that exists in the wrapped_env dictionary.

    Args:
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


def is_text_eq(text: str) -> bool:
    """Check if the given text contains any mathematical expressions.

    Args:
        text (str): The text to be checked for mathematical expressions.

    Returns:
        bool: True if the text contains mathematical expressions, False otherwise.

    Note:
        This function uses a regular expression pattern to match mathematical expressions

    Reference:
        https://www.overleaf.com/learn/latex/Mathematical_expressions
    """
    pattern = r"(\\\(.*?\\\))|(\$.*?\$)|(\\begin\{math\}.*?\\end\{math\})"
    matches = re.findall(pattern, text)

    for match in matches:
        if not re.search(r"\\\$", match[0]):
            return True

    return False
