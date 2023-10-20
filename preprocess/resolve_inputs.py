import os
import re


def resolve_latex_imports(latex_file):
    path = os.path.dirname(latex_file)
    file_content = ""
    with open(latex_file) as f:
        file_content = f.read()

    # Recursively resolve until no more imports found
    while True:
        prev_content = file_content
        file_content = resolve_one_pass(path, file_content)

        if file_content == prev_content:
            break

    with open(latex_file, "w") as f:
        f.write(file_content)


def resolve_one_pass(path, file_content):
    # Find and resolve imports
    input_pattern = r"\\input\{(.*?)\}"
    for match_str in re.finditer(input_pattern, file_content):
        input_file = match_str.group(1)
        if not input_file.endswith(".tex"):
            input_file = input_file + ".tex"
        with open(os.path.join(path, input_file)) as f:
            file_content = file_content.replace(match_str.group(), f.read())

    # Find and resolve imports
    import_pattern = r"\\import\{(.*?)\}"
    for match_str in re.finditer(import_pattern, file_content):
        import_file = match_str.group(1)
        if not import_file.endswith(".tex"):
            import_file = import_file + ".tex"
        with open(os.path.join(path, import_file)) as f:
            file_content = file_content.replace(match_str.group(), f.read())

    # Find and resolve includes
    include_pattern = r"\\include\{(.*?)\}"
    for match_str in re.finditer(include_pattern, file_content):
        include_file = match_str.group(1)
        if not include_file.endswith(".tex"):
            include_file = include_file + ".tex"
        with open(os.path.join(path, include_file)) as f:
            file_content = file_content.replace(match_str.group(), f.read())

    # Find and resolve subimports
    subimport_pattern = r"\\subimport\{(.*?)\}"
    for match_str in re.finditer(subimport_pattern, file_content):
        subimport_file = match_str.group(1)
        if not subimport_file.endswith(".tex"):
            subimport_file = subimport_file + ".tex"
        with open(os.path.join(path, subimport_file)) as f:
            file_content = file_content.replace(match_str.group(), f.read())

    return file_content
