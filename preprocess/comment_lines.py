import re


def comment_sections(latex_file: str):
    """Comment section/subsection lines before begin{document}.

    This function takes a LaTeX file and comments out any lines
    containing \\section or \\subsection that appear before the
    \\begin{document} environment.

    Lines are commented by prepending "% " to them. The modified
    file contents are then written back to the latex_file.

    Args:
        latex_file (str): Path to the LaTeX file

    Returns:
        None

    Remark:
        The file is rewritten in-place with section lines commented
    before \begin{document}.
    """

    with open(latex_file) as f:
        lines = f.readlines()

    section_pattern = r"section|subsection"
    before_doc = True
    commented_lines = []

    for line in lines:
        if line.strip() == "\\begin{document}":
            before_doc = False
            commented_lines.append(line)
            continue

        if before_doc:
            if re.search(section_pattern, line):
                commented_lines.append("% " + line)
            else:
                commented_lines.append(line)
        else:
            commented_lines.append(line)

    with open(latex_file, "w") as f:
        f.write("".join(commented_lines))
