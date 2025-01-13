"""LaTeX document rendering module for colorizing and processing semantic elements."""

from collections import defaultdict
import shutil
from typing import List, Union, Dict
import re
from pathlib import Path
from loguru import logger

from DocParser.vrdu import utils
from DocParser.vrdu.config import config, envs
from DocParser.vrdu.utils import (
    data_from_tex_file,
    tex_file_from_data,
    is_text_eq,
    find_env,
    replace_nth,
)


class Renderer:
    """Handles rendering and colorizing of LaTeX documents.

    This class provides functionality to:
    - Parse and process LaTeX documents
    - Add color definitions and styling
    - Render different semantic elements with distinct colors
    - Generate individual files for each element type
    """

    def __init__(self) -> None:
        """Initialize renderer with empty text storage."""
        self.texts: Dict[str, List[str]] = defaultdict(list)

    def render(self, origin_tex: Path) -> None:
        """Render a colored version of a LaTeX document.

        Args:
            origin_tex: Path to original LaTeX file

        The rendering process:
        1. Creates a colored copy of the original file
        2. Adds required color and layout definitions
        3. Removes any conflicting color definitions
        4. Renders all semantic environments
        5. Generates individual files per element
        6. Exports the rendered text elements
        """
        main_directory = origin_tex.parent
        color_tex = main_directory / "paper_colored.tex"

        # Setup colored document
        shutil.copyfile(origin_tex, color_tex)
        self._setup_document_styling(color_tex)

        # Process environments
        self.render_all_env(color_tex)
        self.render_one_env(main_directory)

        # Export results
        text_file = main_directory / "output/result/texts.json"
        utils.export_to_json(self.texts, text_file)

    def _setup_document_styling(self, color_tex: Path) -> None:
        """Set up document styling by adding color and layout definitions.

        Args:
            color_tex: Path to LaTeX file to modify
        """
        self.add_color_definition(color_tex)
        self.add_layout_definition(color_tex)
        self.remove_predefined_color(color_tex)

    def render_all_env(self, color_tex: Path) -> None:
        """Render all environments in the document.

        Args:
            color_tex: Path to colored LaTeX file
        """
        self.render_simple_envs(color_tex)
        self.render_float_envs(color_tex)

    def render_simple_envs(self, color_tex: Path) -> None:
        """Render simple environments like sections, lists, equations and text.

        Args:
            color_tex: Path to LaTeX file to modify

        Raises:
            EOFError: If TexSoup fails to parse due to runaway environments
            AssertionError: If TexSoup fails due to invalid math mode commands
        """
        data, start, end = data_from_tex_file(color_tex)

        # Process each environment type
        for renderer in [
            self.render_section,
            self.render_list,
            self.render_equation,
            self.render_text,
        ]:
            renderer(data)

        # Write back to file
        tex_file_from_data(data, color_tex, start=start, end=end)

    def render_float_envs(self, tex_file: Path) -> None:
        """Render floating environments like figures, tables, algorithms etc.

        Args:
            tex_file: Path to LaTeX file to modify

        The environments are rendered in a specific order to handle dependencies:
        1. Algorithms
        2. Tables
        3. Code blocks
        4. Footnotes
        5. Graphics
        6. Captions
        7. Title
        8. Abstract
        """
        renderers = [
            self.render_algorithm,
            self.render_tabular,
            self.render_code,
            self.render_footnote,
            self.extract_graphics,
            self.render_caption,
            self.render_title,
            self.render_abstract,
        ]

        for renderer in renderers:
            renderer(tex_file)

    def render_section(self, data: List[Union[dict, str]]) -> None:
        """Render section headings with configured color.

        Args:
            data: LaTeX content as structured data
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
        """Render list environments with configured color.

        Args:
            data: LaTeX content as structured data
        """
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.list_envs)
            if env is None:
                # Process nested lists recursively
                for value in item.values():
                    if isinstance(value, list):
                        self.render_list(value[1])
                continue

            self.texts["List"].append(item[env])
            item[env] = utils.colorize(item[env], "List")

    def render_equation(self, data: List[Union[dict, str]]) -> None:
        """Render equation environments with configured color.

        Args:
            data: LaTeX content as structured data
        """
        for item in data:
            if not isinstance(item, dict):
                continue

            env = find_env(item, envs.math_envs)
            if env is None:
                # Process nested equations
                for value in item.values():
                    if isinstance(value, list):
                        self.render_equation(value[1])
                continue

            self.texts["Equation"].append(item[env])
            item[env] = utils.colorize(item[env], "Equation")

    def render_text(self, data: List[Union[dict, str]]) -> None:
        """Render text content with configured colors.

        Handles both regular text and text containing equations.

        Args:
            data: LaTeX content as structured data
        """
        for index, item in enumerate(data):
            if not isinstance(item, str):
                if isinstance(item, dict):
                    for key, value in item.items():
                        if key.lower() in envs.text_envs and isinstance(value, list):
                            self.render_text(value[1])
                continue

            if not item or item.isspace():
                continue

            # Determine text type and colorize
            text_type = "Text-EQ" if is_text_eq(item) else "Text"
            colored_text = utils.colorize(item, text_type)
            self.texts[text_type].append(item)

            # Preserve whitespace
            if item[0] == "\n":
                colored_text = "\n" + colored_text
            if item[-1] == "\n":
                colored_text += "\n"

            data[index] = colored_text

    def add_color_definition(self, color_tex: Path) -> None:
        """Add color package and definitions to LaTeX file.

        Args:
            color_tex: Path to LaTeX file to modify

        Raises:
            ValueError: If document begin tag not found
        """
        content = color_tex.read_text()

        # Build color definitions
        definitions = ["\\usepackage{xcolor}"]
        for name, rgb_color in config.name2rgbcolor.items():
            color_name = config.name2color[name]
            r, g, b = rgb_color
            definition = f"\\definecolor{{{color_name}}}{{RGB}}{{{r}, {g}, {b}}}"
            definitions.append(definition)

        color_definitions = "\n" + "\n".join(definitions) + "\n"

        # Insert at document begin
        preamble = re.search(r"\\begin{document}", content)
        if not preamble:
            raise ValueError("Document begin tag not found")

        content = (
            content[: preamble.start()]
            + color_definitions
            + content[preamble.start() :]
        )

        color_tex.write_text(content)

    def add_layout_definition(self, color_tex: Path) -> None:
        """Add layout definitions to LaTeX file.

        Args:
            color_tex: Path to LaTeX file to modify

        Raises:
            ValueError: If document end tag not found

        Reference:
            https://www.overleaf.com/learn/latex/Page_size_and_margins
        """
        content = color_tex.read_text()

        # Build layout definitions
        definitions = ["\\message{[vrdu_data_process: Info]}"]
        for key in config.layout_keys:
            definition = f"\\message{{[vrdu_data_process: The {key} is: \\the\\{key}]}}"
            definitions.append(definition)

        layout_definitions = "\n" + "\n".join(definitions) + "\n"

        # Insert before document end
        doc_end = re.search(r"\\end{document}", content)
        if not doc_end:
            raise ValueError("Document end tag not found")

        content = (
            content[: doc_end.start()] + layout_definitions + content[doc_end.start() :]
        )

        color_tex.write_text(content)

    def remove_predefined_color(self, color_tex: Path) -> None:
        """Remove hyperref and lstlisting color settings.

        Args:
            color_tex: Path to LaTeX file to modify

        Raises:
            ValueError: If document begin tag not found

        Reference:
            https://www.overleaf.com/learn/latex/Hyperlinks
        """
        content = color_tex.read_text()

        # Find document begin
        preamble = re.search(r"\\begin{document}", content)
        if not preamble:
            raise ValueError("Document begin tag not found")

        # Disable hyperref colors if present
        hyperref_pattern = (
            r"\\usepackage{hyperref}|\\usepackage(\[)?\[.*?\]?(\])?{hyperref}"
        )
        if re.search(hyperref_pattern, content[: preamble.start()]):
            content = (
                content[: preamble.start()]
                + "\\hypersetup{colorlinks=false}\n"
                + content[preamble.start() :]
            )

        # Remove lstlisting colors
        content = re.sub(r"\\lstset\{.*?\}", "", content)

        color_tex.write_text(content)

    def modify_color_definitions(self, input_file: Path, output_file: Path) -> None:
        """Modify color definitions to white in output file.

        Args:
            input_file: Source LaTeX file path
            output_file: Destination LaTeX file path
        """
        content = input_file.read_text()

        # Replace each color with white
        for name in config.name2rgbcolor:
            color_name = config.name2color[name]
            pattern = rf"\\definecolor{{{color_name}}}{{RGB}}{{(\d+), (\d+), (\d+)}}"
            content = re.sub(
                pattern,
                rf"\\definecolor{{{color_name}}}{{RGB}}{{255, 255, 255}}",
                content,
            )

        output_file.write_text(content)

    def get_env_orders(self, tex_file: Path) -> List[str]:
        """Get ordered list of environments from file.

        Args:
            tex_file: Path to LaTeX file

        Returns:
            List of environment names in order of appearance
        """
        contents = tex_file.read_text()

        colors = list(config.name2color.values())
        pattern = "|".join(rf"\b{re.escape(term)}\b" for term in colors)
        matches = [m.group(0) for m in re.finditer(pattern, contents)]

        # Skip color definitions at start
        return matches[len(colors) :]

    def render_one_env(self, main_directory: Path) -> None:
        """Render individual files with one environment highlighted.

        Args:
            main_directory: Working directory path
        """
        color_tex = main_directory / "paper_colored.tex"
        white_tex = main_directory / "paper_white.tex"

        self.modify_color_definitions(color_tex, white_tex)
        ordered_envs = self.get_env_orders(white_tex)

        content = white_tex.read_text()

        index_map = defaultdict(int)
        suffix = "_color"

        for i, env_color in enumerate(ordered_envs):
            env = env_color[: -len(suffix)]
            env_count = index_map[env]

            # Replace nth occurrence with black
            new_content = replace_nth(
                content, "{" + env_color + "}", "{black}", env_count + 2
            )

            # Generate output filename
            output_file = (
                main_directory
                / f"paper_{config.folder_prefix}_{str(i).zfill(5)}_{env}_{str(env_count).zfill(5)}.tex"
            )

            output_file.write_text(new_content)

            index_map[env] += 1

    def render_caption(self, tex_file: Path) -> None:
        """Render captions with color.

        Args:
            tex_file: Path to LaTeX file
        """
        content = tex_file.read_text()

        pattern = r"\\caption(?:\[[^\]]*\])?(?:\{[^}]*\})"
        result = self._render_simple_envs(content, pattern, "Caption")

        tex_file.write_text(result)

    def render_title(self, tex_file: Path) -> None:
        """Render document title with color.

        Args:
            tex_file: Path to LaTeX file
        """
        content = tex_file.read_text()

        pattern = r"\\title(?:\{[^}]*\})"
        result = self._render_simple_envs(content, pattern, "PaperTitle")

        tex_file.write_text(result)

    def render_footnote(self, tex_file: Path) -> None:
        """Render footnotes with color.

        Args:
            tex_file: Path to LaTeX file
        """
        content = tex_file.read_text()

        for env_name in envs.footnote_envs:
            pattern = r"\\" + env_name + r"(?:\[[^\]]*\])?(?:\{[^}]*\})"
            content = self._render_simple_envs(content, pattern, "Footnote")

        tex_file.write_text(content)

    def _render_simple_envs(self, content: str, pattern: str, category: str) -> str:
        """Render simple environments with color.

        Args:
            content: LaTeX content
            pattern: Regex pattern to match
            category: Environment category name

        Returns:
            Modified content with colored environments
        """
        matches = re.finditer(pattern, content)
        result = ""
        last_end = 0

        for match in matches:
            start = match.start()
            end = match.end()

            # Handle nested brackets
            num_left = content[start:end].count("{")
            num_right = content[start:end].count("}")

            while num_right < num_left:
                if content[end] == "{":
                    num_left += 1
                elif content[end] == "}":
                    num_right += 1
                end += 1

            env_content = content[start:end]
            self.texts[category].append(env_content)

            result += content[last_end:start]
            result += utils.colorize(env_content, category)
            last_end = end

        result += content[last_end:]
        return result

    def render_abstract(self, tex_file: Path) -> None:
        """Render abstract with color.

        Args:
            tex_file: Path to LaTeX file

        Raises:
            ValueError: If multiple abstracts found
        """
        content = tex_file.read_text()

        pattern = r"\\begin{abstract}.*?\\end{abstract}"
        matches = list(re.finditer(pattern, content, re.DOTALL))

        if len(matches) > 1:
            raise ValueError("Multiple abstracts found")

        if not matches:
            return

        match = matches[0]
        abstract = content[match.start() : match.end()]
        self.texts["Abstract"].append(abstract)

        result = (
            content[: match.start()]
            + utils.colorize(abstract, "Abstract")
            + content[match.end() :]
        )

        tex_file.write_text(result)

    def render_tabular(self, tex_file: Path) -> None:
        """Render tables with color.

        Args:
            tex_file: Path to LaTeX file
        """
        content = tex_file.read_text()

        pattern = r"\\begin{(tabular[*xy]?)}.*?\\end{\1}"
        result = self._render_float_envs(content, pattern, "Table")

        tex_file.write_text(result)

    def render_algorithm(self, tex_file: Path) -> None:
        """Render algorithms with color.

        Args:
            tex_file: Path to LaTeX file
        """
        content = tex_file.read_text()

        pattern = r"\\begin{algorithm[*]?}(.*?)\\end{algorithm[*]?}"
        result = self._render_float_envs(content, pattern, "Algorithm")

        tex_file.write_text(result)

    def render_code(self, tex_file: Path) -> None:
        """Render code blocks with color.

        Handles both code environments and lstinputlisting.

        Args:
            tex_file: Path to LaTeX file

        Reference:
            https://en.wikibooks.org/wiki/LaTeX/Source_Code_Listings
        """
        content = tex_file.read_text()

        patterns = [
            r"\\begin{(verbatim|lstlisting|program)[*]?}(.*?)\\end{\1[*]?}",
            r"\\lstinputlisting\[[^\]]*\]{[^\}]*}",
        ]
        pattern = "|".join(patterns)

        result = self._render_float_envs(content, pattern, "Code")

        tex_file.write_text(result)

    def _render_float_envs(self, content: str, pattern: str, category: str) -> str:
        """Render floating environments with color.

        Args:
            content: LaTeX content
            pattern: Regex pattern to match
            category: Environment category name

        Returns:
            Modified content with colored environments
        """
        matches = list(re.finditer(pattern, content, re.DOTALL))

        if not matches:
            logger.debug(f"No {category} environments found")
            return content

        result = content[: matches[0].start()]

        for i, match in enumerate(matches):
            if i > 0:
                result += content[matches[i - 1].end() : match.start()]

            env_content = content[match.start() : match.end()]

            # Skip figures in tables
            if category == "Table" and "\\includegraphics" in env_content:
                continue

            self.texts[category].append(env_content)
            result += utils.colorize(env_content, category)

        result += content[matches[-1].end() :]
        return result

    def extract_graphics(self, tex_file: Path) -> None:
        """Extract graphics commands.

        Args:
            tex_file: Path to LaTeX file
        """
        content = tex_file.read_text()

        pattern = r"\\includegraphics(?:\[(.*?)\])?{(.*?)}"
        for options, path in re.findall(pattern, content):
            graphic = "\\includegraphics"
            if options:
                graphic += f"[{options}]"
            graphic += f"{{{path}}}"
            self.texts["Figure"].append(graphic)
