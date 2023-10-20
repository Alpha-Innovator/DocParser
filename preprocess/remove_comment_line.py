import re


def remove_comment_line(latex_file):
    # Regular expression pattern to match LaTeX comments
    comment_pattern = r"(?<!\\)%.*?$"

    # Read the LaTeX file
    with open(latex_file, "r") as file:
        content = file.read()

    # Remove comments using regular expression substitution
    content = re.sub(comment_pattern, "", content, flags=re.MULTILINE)

    # Write the modified content back to the LaTeX file
    with open(latex_file, "w") as file:
        file.write(content)
